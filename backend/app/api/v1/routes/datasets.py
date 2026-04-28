from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, Query, Request, UploadFile
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_user
from app.api.v1.route_helpers import apply_cursor, get_dataset_for_user, get_project_for_user, next_cursor
from app.core.database import get_db_session
from app.core.errors import AppError
from app.models.enums import UserRole
from app.models.dataset import Dataset
from app.models.project import Project
from app.models.user import User
from app.services.storage.service import LocalStorageService, parse_protected_columns
from app.utils.audit_log import create_audit_log
from app.utils.response import envelope
from app.utils.serialization import dataset_to_dict

router = APIRouter()
storage_service = LocalStorageService()


@router.post("/projects/{project_id}/datasets")
async def upload_dataset(
    project_id: str,
    request: Request,
    file: UploadFile = File(...),
    target_column: str = Form(...),
    protected_columns: str = Form(...),
    positive_label: str = Form(...),
    prediction_column: str | None = Form(default=None),
    score_column: str | None = Form(default=None),
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    if current_user.role == UserRole.VIEWER:
        raise AppError(code="forbidden", message="Viewers cannot upload datasets.", status_code=403)
    project = await get_project_for_user(session, project_id, current_user)
    protected = parse_protected_columns(protected_columns)
    stored = await storage_service.save_dataset(
        file,
        target_column,
        protected,
        positive_label,
        prediction_column,
        score_column,
    )
    dataset = Dataset(
        project_id=project.id,
        filename=stored.filename,
        file_path=stored.file_path,
        file_hash=stored.file_hash,
        row_count=stored.row_count,
        col_count=stored.col_count,
        target_column=target_column,
        protected_columns=protected,
        positive_label=str(positive_label),
        uploaded_at=datetime.now(UTC),
        expires_at=stored.expires_at or datetime.now(UTC),
        column_types=stored.column_types or {},
        prediction_column=prediction_column,
        score_column=score_column,
    )
    session.add(dataset)
    await session.flush()
    await create_audit_log(session, current_user.id, "upload_dataset", "dataset", dataset.id, {"project_id": project.id})
    await session.commit()
    await session.refresh(dataset)
    return envelope(request, dataset_to_dict(dataset))


@router.get("/projects/{project_id}/datasets")
async def list_datasets(
    project_id: str,
    request: Request,
    cursor: str | None = Query(default=None),
    limit: int = Query(default=20, le=50),
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    project = await get_project_for_user(session, project_id, current_user)
    query = select(Dataset).where(Dataset.project_id == project.id).order_by(desc(Dataset.uploaded_at), desc(Dataset.id))
    query = apply_cursor(query, Dataset, "uploaded_at", cursor).limit(limit + 1)
    datasets = list((await session.execute(query)).scalars().all())
    has_more = len(datasets) > limit
    items = datasets[:limit]
    return envelope(
        request,
        [dataset_to_dict(item) for item in items],
        next_cursor(items, "uploaded_at") if has_more else None,
    )


@router.get("/datasets/{dataset_id}")
async def get_dataset(
    dataset_id: str,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    dataset = await get_dataset_for_user(session, dataset_id, current_user)
    return envelope(request, dataset_to_dict(dataset))


@router.get("/datasets/{dataset_id}/preview")
async def dataset_preview(
    dataset_id: str,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    dataset = await get_dataset_for_user(session, dataset_id, current_user)
    preview_rows, column_types = storage_service.preview_dataframe(Path(dataset.file_path), dataset.filename)
    return envelope(
        request,
        {"dataset_id": dataset.id, "preview_rows": preview_rows, "column_types": column_types},
    )


@router.delete("/datasets/{dataset_id}")
async def delete_dataset(
    dataset_id: str,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    query = select(Dataset).options(selectinload(Dataset.audit_runs)).where(Dataset.id == dataset_id)
    dataset = (await session.execute(query)).scalar_one_or_none()
    if dataset is None:
        raise AppError(code="dataset_not_found", message="Dataset not found.", status_code=404)
    project = await get_project_for_user(session, dataset.project_id, current_user)
    if current_user.role == UserRole.VIEWER:
        raise AppError(code="forbidden", message="Viewers cannot delete datasets.", status_code=403)
    if dataset.audit_runs:
        raise AppError(
            code="dataset_in_use",
            message="Datasets with audit history cannot be deleted.",
            status_code=409,
        )
    await session.delete(dataset)
    await create_audit_log(session, current_user.id, "delete_dataset", "dataset", dataset.id, {"project_id": project.id})
    await session.commit()
    return envelope(request, {"success": True})
