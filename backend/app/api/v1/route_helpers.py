from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import Select, and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.errors import AppError
from app.models.audit import AuditLog, AuditRun, Notification
from app.models.dataset import Dataset, ModelArtifact
from app.models.enums import UserRole
from app.models.project import Project
from app.models.report import Report
from app.models.user import User
from app.utils.pagination import decode_cursor, encode_cursor


async def get_project_for_user(
    session: AsyncSession, project_id: str, user: User, with_relations: bool = False
) -> Project:
    query = select(Project).where(Project.id == project_id)
    if with_relations:
        query = query.options(
            selectinload(Project.datasets),
            selectinload(Project.models),
            selectinload(Project.audit_runs),
            selectinload(Project.notifications),
        )
    if user.role != UserRole.ADMIN:
        query = query.where(Project.user_id == user.id)
    project = (await session.execute(query)).scalar_one_or_none()
    if project is None:
        raise AppError(code="project_not_found", message="Project not found.", status_code=404)
    return project


async def get_dataset_for_user(session: AsyncSession, dataset_id: str, user: User) -> Dataset:
    query = select(Dataset).join(Project).where(Dataset.id == dataset_id)
    if user.role != UserRole.ADMIN:
        query = query.where(Project.user_id == user.id)
    dataset = (await session.execute(query)).scalar_one_or_none()
    if dataset is None:
        raise AppError(code="dataset_not_found", message="Dataset not found.", status_code=404)
    return dataset


async def get_model_for_user(session: AsyncSession, model_id: str, user: User) -> ModelArtifact:
    query = select(ModelArtifact).join(Project).where(ModelArtifact.id == model_id)
    if user.role != UserRole.ADMIN:
        query = query.where(Project.user_id == user.id)
    model = (await session.execute(query)).scalar_one_or_none()
    if model is None:
        raise AppError(code="model_not_found", message="Model not found.", status_code=404)
    return model


async def get_run_for_user(
    session: AsyncSession, run_id: str, user: User, with_results: bool = False
) -> AuditRun:
    query = select(AuditRun).join(Project).where(AuditRun.id == run_id)
    if with_results:
        query = query.options(selectinload(AuditRun.results), selectinload(AuditRun.reports))
    if user.role != UserRole.ADMIN:
        query = query.where(Project.user_id == user.id)
    run = (await session.execute(query)).scalar_one_or_none()
    if run is None:
        raise AppError(code="run_not_found", message="Audit run not found.", status_code=404)
    return run


def apply_cursor(query: Select, model, timestamp_field_name: str, cursor: str | None) -> Select:
    if cursor is None:
        return query
    created_at, entity_id = decode_cursor(cursor)
    timestamp_field = getattr(model, timestamp_field_name)
    return query.where(
        or_(
            timestamp_field < created_at,
            and_(timestamp_field == created_at, model.id < entity_id),
        )
    )


def next_cursor(items: list[object], timestamp_field_name: str) -> str | None:
    if not items:
        return None
    last_item = items[-1]
    timestamp = getattr(last_item, timestamp_field_name)
    if timestamp is None:
        timestamp = datetime.now(UTC)
    return encode_cursor(timestamp, last_item.id)

