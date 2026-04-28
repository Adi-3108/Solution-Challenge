from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from app.models.enums import ModelType


class DatasetResponse(BaseModel):
    id: str
    project_id: str
    filename: str
    file_hash: str
    row_count: int
    col_count: int
    target_column: str
    protected_columns: list[str]
    positive_label: str
    prediction_column: str | None
    score_column: str | None
    uploaded_at: datetime
    expires_at: datetime
    column_types: dict[str, str]

    model_config = {"from_attributes": True}


class DatasetPreviewResponse(BaseModel):
    dataset_id: str
    preview_rows: list[dict[str, object]]
    column_types: dict[str, str]


class ModelArtifactResponse(BaseModel):
    id: str
    project_id: str
    filename: str
    file_hash: str
    model_type: ModelType
    uploaded_at: datetime

    model_config = {"from_attributes": True}

