from __future__ import annotations

import hashlib
import io
import json
import pickle
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4

import joblib
import pandas as pd
from fastapi import UploadFile

from app.core.config import settings
from app.core.errors import AppError
from app.models.enums import ModelType


@dataclass(slots=True)
class StoredFile:
    filename: str
    file_path: str
    file_hash: str
    row_count: int = 0
    col_count: int = 0
    column_types: dict[str, str] | None = None
    expires_at: datetime | None = None


class LocalStorageService:
    def __init__(self) -> None:
        self.base_path = settings.file_storage_path
        self.base_path.mkdir(parents=True, exist_ok=True)

    async def save_dataset(
        self,
        upload: UploadFile,
        target_column: str,
        protected_columns: list[str],
        positive_label: str,
        prediction_column: str | None = None,
        score_column: str | None = None,
    ) -> StoredFile:
        content = await self._read_and_validate(upload, {"csv", "json", "parquet"})
        stored_path = self._write_file(content, upload.filename or "dataset", "datasets")
        dataframe = self.load_dataframe(Path(stored_path), upload.filename or "dataset")
        self._validate_dataset_columns(
            dataframe,
            target_column,
            protected_columns,
            prediction_column,
            score_column,
        )
        return StoredFile(
            filename=upload.filename or "dataset",
            file_path=stored_path,
            file_hash=self._hash_bytes(content),
            row_count=int(len(dataframe.index)),
            col_count=int(len(dataframe.columns)),
            column_types=infer_column_types(dataframe),
            expires_at=datetime.now(UTC) + timedelta(days=settings.allowed_file_retention_days),
        )

    async def save_model(self, upload: UploadFile) -> tuple[StoredFile, ModelType]:
        filename = upload.filename or "model"
        content = await self._read_and_validate(upload, {"pkl", "joblib", "onnx"})
        stored_path = self._write_file(content, filename, "models")
        suffix = filename.rsplit(".", maxsplit=1)[-1].lower()
        return (
            StoredFile(
                filename=filename,
                file_path=stored_path,
                file_hash=self._hash_bytes(content),
                expires_at=datetime.now(UTC) + timedelta(days=settings.allowed_file_retention_days),
            ),
            ModelType(suffix),
        )

    def load_dataframe(self, path: Path, filename: str) -> pd.DataFrame:
        suffix = filename.rsplit(".", maxsplit=1)[-1].lower()
        if suffix == "csv":
            return pd.read_csv(path)
        if suffix == "json":
            try:
                return pd.read_json(path)
            except ValueError:
                return pd.read_json(path, lines=True)
        if suffix == "parquet":
            return pd.read_parquet(path)
        raise AppError(code="unsupported_file", message="Unsupported dataset file type.", status_code=400)

    def load_model(self, path: Path, model_type: ModelType) -> object | None:
        if model_type == ModelType.JOBLIB:
            return joblib.load(path)
        if model_type == ModelType.PICKLE:
            with path.open("rb") as handle:
                return pickle.load(handle)
        return None

    def preview_dataframe(self, path: Path, filename: str) -> tuple[list[dict[str, object]], dict[str, str]]:
        dataframe = self.load_dataframe(path, filename)
        preview = dataframe.head(100).replace({pd.NA: None}).to_dict(orient="records")
        return preview, infer_column_types(dataframe)

    def _validate_dataset_columns(
        self,
        dataframe: pd.DataFrame,
        target_column: str,
        protected_columns: list[str],
        prediction_column: str | None,
        score_column: str | None,
    ) -> None:
        expected = [target_column, *protected_columns]
        if prediction_column:
            expected.append(prediction_column)
        if score_column:
            expected.append(score_column)
        missing = [column for column in expected if column not in dataframe.columns]
        if missing:
            raise AppError(
                code="invalid_dataset",
                message="The uploaded dataset is missing required columns.",
                status_code=400,
                details={"missing_columns": missing},
            )

    async def _read_and_validate(self, upload: UploadFile, allowed_extensions: set[str]) -> bytes:
        filename = upload.filename or "upload"
        extension = filename.rsplit(".", maxsplit=1)[-1].lower()
        if extension not in allowed_extensions:
            raise AppError(code="unsupported_file", message="Unsupported file type.", status_code=400)
        content = await upload.read()
        max_bytes = settings.max_file_size_mb * 1024 * 1024
        if len(content) > max_bytes:
            raise AppError(code="file_too_large", message="File exceeds the maximum allowed size.", status_code=413)
        self._scan_for_malicious_content(filename, content)
        return content

    def _scan_for_malicious_content(self, filename: str, content: bytes) -> None:
        lower_name = filename.lower()
        lower_body = content[:4096].decode("latin-1", errors="ignore").lower()
        blocked_tokens = ["<script", "powershell", "cmd.exe", "javascript:"]
        if any(token in lower_body for token in blocked_tokens):
            raise AppError(code="malicious_file", message="The uploaded file failed security scanning.", status_code=400)
        if not lower_name.endswith((".pkl", ".joblib", ".onnx")) and content.startswith(b"MZ"):
            raise AppError(code="malicious_file", message="Executable content is not allowed.", status_code=400)

    def _write_file(self, content: bytes, original_name: str, bucket: str) -> str:
        suffix = original_name.rsplit(".", maxsplit=1)[-1].lower()
        random_name = f"{uuid4()}.{suffix}"
        destination = self.base_path / bucket / random_name
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(content)
        return str(destination)

    def _hash_bytes(self, content: bytes) -> str:
        return hashlib.sha256(content).hexdigest()


def infer_column_types(dataframe: pd.DataFrame) -> dict[str, str]:
    return {column: str(dtype) for column, dtype in dataframe.dtypes.items()}


def parse_protected_columns(raw: str) -> list[str]:
    try:
        parsed = json.loads(raw)
        if isinstance(parsed, list):
            return [str(item) for item in parsed]
    except json.JSONDecodeError:
        pass
    return [item.strip() for item in raw.split(",") if item.strip()]

