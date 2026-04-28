from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.api.v1.route_helpers import get_project_for_user
from app.core.database import get_db_session
from app.core.errors import AppError
from app.models.audit import Notification
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.notification import NotificationUpdateRequest
from app.utils.audit_log import create_audit_log
from app.utils.response import envelope

router = APIRouter()


@router.get("/projects/{project_id}/notifications")
async def list_notifications(
    project_id: str,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    project = await get_project_for_user(session, project_id, current_user)
    rows = (await session.execute(select(Notification).where(Notification.project_id == project.id))).scalars().all()
    return envelope(
        request,
        [
            {
                "id": row.id,
                "project_id": row.project_id,
                "type": row.type.value,
                "destination": row.destination,
                "enabled": row.enabled,
            }
            for row in rows
        ],
    )


@router.put("/projects/{project_id}/notifications")
async def update_notifications(
    project_id: str,
    payload: NotificationUpdateRequest,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    project = await get_project_for_user(session, project_id, current_user)
    if current_user.role == UserRole.VIEWER:
        raise AppError(code="forbidden", message="Viewers cannot update notifications.", status_code=403)
    await session.execute(delete(Notification).where(Notification.project_id == project.id))
    for item in payload.notifications:
        session.add(
            Notification(
                project_id=project.id,
                type=item.type,
                destination=item.destination,
                enabled=item.enabled,
            )
        )
    await create_audit_log(session, current_user.id, "update_notifications", "project", project.id, {})
    await session.commit()
    return envelope(request, {"success": True})
