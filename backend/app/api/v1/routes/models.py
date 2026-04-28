from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, File, Query, Request, UploadFile
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_user
from app.api.v1.route_helpers import apply_cursor, get_model_for_user, get_project_for_user, next_cursor
from app.core.database import get_db_session
from app.core.errors import AppError
from app.models.dataset import ModelArtifact
from app.models.enums import UserRole
from app.models.user import User
from app.services.storage.service import LocalStorageService
from app.utils.audit_log import create_audit_log
from app.utils.response import envelope
from app.utils.serialization import model_to_dict

router = APIRouter()
storage_service = LocalStorageService()


@router.post("/projects/{project_id}/models")
async def upload_model(
    project_id: str,
    request: Request,
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    if current_user.role == UserRole.VIEWER:
        raise AppError(code="forbidden", message="Viewers cannot upload models.", status_code=403)
    project = await get_project_for_user(session, project_id, current_user)
    stored, model_type = await storage_service.save_model(file)
    model = ModelArtifact(
        project_id=project.id,
        filename=stored.filename,
        file_path=stored.file_path,
        file_hash=stored.file_hash,
        model_type=model_type,
        uploaded_at=datetime.now(UTC),
    )
    session.add(model)
    await session.flush()
    await create_audit_log(session, current_user.id, "upload_model", "model", model.id, {"project_id": project.id})
    await session.commit()
    await session.refresh(model)
    return envelope(request, model_to_dict(model))


@router.get("/projects/{project_id}/models")
async def list_models(
    project_id: str,
    request: Request,
    cursor: str | None = Query(default=None),
    limit: int = Query(default=20, le=50),
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    project = await get_project_for_user(session, project_id, current_user)
    query = select(ModelArtifact).where(ModelArtifact.project_id == project.id).order_by(desc(ModelArtifact.uploaded_at), desc(ModelArtifact.id))
    query = apply_cursor(query, ModelArtifact, "uploaded_at", cursor).limit(limit + 1)
    models = list((await session.execute(query)).scalars().all())
    has_more = len(models) > limit
    items = models[:limit]
    return envelope(
        request,
        [model_to_dict(item) for item in items],
        next_cursor(items, "uploaded_at") if has_more else None,
    )


@router.delete("/models/{model_id}")
async def delete_model(
    model_id: str,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    query = select(ModelArtifact).options(selectinload(ModelArtifact.audit_runs)).where(ModelArtifact.id == model_id)
    model = (await session.execute(query)).scalar_one_or_none()
    if model is None:
        raise AppError(code="model_not_found", message="Model not found.", status_code=404)
    await get_project_for_user(session, model.project_id, current_user)
    if current_user.role == UserRole.VIEWER:
        raise AppError(code="forbidden", message="Viewers cannot delete models.", status_code=403)
    if model.audit_runs:
        raise AppError(
            code="model_in_use",
            message="Models referenced by audit runs cannot be deleted.",
            status_code=409,
        )
    await session.delete(model)
    await create_audit_log(session, current_user.id, "delete_model", "model", model.id, {"project_id": model.project_id})
    await session.commit()
    return envelope(request, {"success": True})
