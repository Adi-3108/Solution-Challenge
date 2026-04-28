from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_roles
from app.api.v1.route_helpers import apply_cursor, next_cursor
from app.core.database import get_db_session
from app.core.errors import AppError
from app.models.audit import AuditLog
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.admin import UserRoleUpdateRequest
from app.utils.audit_log import create_audit_log
from app.utils.response import envelope

router = APIRouter()


@router.get("/audit-log")
async def audit_log(
    request: Request,
    cursor: str | None = Query(default=None),
    limit: int = Query(default=20, le=50),
    action: str | None = Query(default=None),
    resource_type: str | None = Query(default=None),
    session: AsyncSession = Depends(get_db_session),
    _: User = Depends(require_roles(UserRole.ADMIN)),
):
    query = select(AuditLog).order_by(desc(AuditLog.created_at), desc(AuditLog.id))
    if action:
        query = query.where(AuditLog.action == action)
    if resource_type:
        query = query.where(AuditLog.resource_type == resource_type)
    query = apply_cursor(query, AuditLog, "created_at", cursor).limit(limit + 1)
    logs = list((await session.execute(query)).scalars().all())
    has_more = len(logs) > limit
    items = logs[:limit]
    payload = [
        {
            "id": row.id,
            "user_id": row.user_id,
            "action": row.action,
            "resource_type": row.resource_type,
            "resource_id": row.resource_id,
            "metadata": row.metadata_json,
            "created_at": row.created_at.isoformat(),
        }
        for row in items
    ]
    return envelope(request, payload, next_cursor(items, "created_at") if has_more else None)


@router.get("/users")
async def list_users(
    request: Request,
    cursor: str | None = Query(default=None),
    limit: int = Query(default=20, le=50),
    session: AsyncSession = Depends(get_db_session),
    _: User = Depends(require_roles(UserRole.ADMIN)),
):
    query = select(User).order_by(desc(User.created_at), desc(User.id))
    query = apply_cursor(query, User, "created_at", cursor).limit(limit + 1)
    users = list((await session.execute(query)).scalars().all())
    has_more = len(users) > limit
    items = users[:limit]
    payload = [
        {
            "id": user.id,
            "email": user.email,
            "role": user.role.value,
            "created_at": user.created_at.isoformat(),
            "deleted_at": user.deleted_at.isoformat() if user.deleted_at else None,
        }
        for user in items
    ]
    return envelope(request, payload, next_cursor(items, "created_at") if has_more else None)


@router.patch("/users/{user_id}")
async def update_user(
    user_id: str,
    payload: UserRoleUpdateRequest,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
):
    user = (await session.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
    if user is None:
        raise AppError(code="user_not_found", message="User not found.", status_code=404)
    user.role = payload.role
    await create_audit_log(session, current_user.id, "update_user_role", "user", user.id, {"role": payload.role.value})
    await session.commit()
    await session.refresh(user)
    return envelope(
        request,
        {
            "id": user.id,
            "email": user.email,
            "role": user.role.value,
            "created_at": user.created_at.isoformat(),
        },
    )

