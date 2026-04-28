from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_user
from app.api.v1.route_helpers import apply_cursor, get_project_for_user, next_cursor
from app.core.database import get_db_session
from app.core.errors import AppError
from app.models.enums import UserRole
from app.models.project import Project
from app.models.user import User
from app.schemas.project import ProjectCreate, ProjectUpdate
from app.utils.audit_log import create_audit_log
from app.utils.response import envelope
from app.utils.sanitize import sanitize_text
from app.utils.serialization import dataset_to_dict, model_to_dict, project_to_dict, run_to_dict

router = APIRouter()


@router.get("")
async def list_projects(
    request: Request,
    cursor: str | None = Query(default=None),
    limit: int = Query(default=20, le=50),
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    query = select(Project).options(selectinload(Project.audit_runs)).order_by(desc(Project.created_at), desc(Project.id))
    if current_user.role != UserRole.ADMIN:
        query = query.where(Project.user_id == current_user.id)
    query = apply_cursor(query, Project, "created_at", cursor).limit(limit + 1)
    projects = list((await session.execute(query)).scalars().all())
    has_more = len(projects) > limit
    items = projects[:limit]
    return envelope(
        request,
        [project_to_dict(project) for project in items],
        next_cursor(items, "created_at") if has_more else None,
    )


@router.post("")
async def create_project(
    payload: ProjectCreate,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    if current_user.role == UserRole.VIEWER:
        raise AppError(code="forbidden", message="Viewers cannot create projects.", status_code=403)
    project = Project(
        user_id=current_user.id,
        name=sanitize_text(payload.name) or payload.name,
        description=sanitize_text(payload.description),
    )
    session.add(project)
    await session.flush()
    await create_audit_log(session, current_user.id, "create_project", "project", project.id, {})
    await session.commit()
    await session.refresh(project)
    return envelope(request, project_to_dict(project))


@router.get("/{project_id}")
async def get_project(
    project_id: str,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    project = await get_project_for_user(session, project_id, current_user, with_relations=True)
    data = project_to_dict(project)
    data["datasets"] = [dataset_to_dict(dataset) for dataset in project.datasets]
    data["models"] = [model_to_dict(model) for model in project.models]
    data["runs"] = [
        run_to_dict(run)
        for run in sorted(
            project.audit_runs,
            key=lambda item: item.started_at or item.completed_at or project.created_at,
            reverse=True,
        )
    ]
    return envelope(request, data)


@router.patch("/{project_id}")
async def update_project(
    project_id: str,
    payload: ProjectUpdate,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    project = await get_project_for_user(session, project_id, current_user)
    if current_user.role == UserRole.VIEWER:
        raise AppError(code="forbidden", message="Viewers cannot edit projects.", status_code=403)
    if payload.name is not None:
        project.name = sanitize_text(payload.name) or project.name
    if payload.description is not None:
        project.description = sanitize_text(payload.description)
    if payload.archived_at is not None:
        project.archived_at = payload.archived_at
    await create_audit_log(session, current_user.id, "update_project", "project", project.id, {})
    await session.commit()
    await session.refresh(project)
    return envelope(request, project_to_dict(project))


@router.delete("/{project_id}")
async def delete_project(
    project_id: str,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    project = await get_project_for_user(session, project_id, current_user)
    if current_user.role == UserRole.VIEWER:
        raise AppError(code="forbidden", message="Viewers cannot archive projects.", status_code=403)
    project.archived_at = datetime.now(UTC)
    await create_audit_log(session, current_user.id, "archive_project", "project", project.id, {})
    await session.commit()
    return envelope(request, {"success": True})
