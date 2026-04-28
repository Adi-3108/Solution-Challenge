from __future__ import annotations

from fastapi import Depends, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.errors import AppError
from app.core.security import ACCESS_COOKIE_NAME, TokenType, decode_token
from app.models.enums import UserRole
from app.models.user import User


def extract_request_id(request: Request) -> str:
    return getattr(request.state, "request_id", "unknown")


def get_token_from_request(request: Request) -> str:
    cookie_token = request.cookies.get(ACCESS_COOKIE_NAME)
    if cookie_token:
        return cookie_token
    authorization = request.headers.get("Authorization", "")
    if authorization.startswith("Bearer "):
        return authorization.replace("Bearer ", "", 1)
    raise AppError(code="unauthorized", message="Authentication required.", status_code=401)


async def get_current_user(
    request: Request, session: AsyncSession = Depends(get_db_session)
) -> User:
    token = get_token_from_request(request)
    try:
        email = decode_token(token, TokenType.ACCESS)
    except ValueError as exc:
        raise AppError(code="unauthorized", message="Authentication required.", status_code=401) from exc
    result = await session.execute(select(User).where(User.email == email, User.deleted_at.is_(None)))
    user = result.scalar_one_or_none()
    if user is None:
        raise AppError(code="unauthorized", message="Invalid user session.", status_code=401)
    request.state.user_id = user.id
    return user


def require_roles(*roles: UserRole):
    async def dependency(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in roles:
            raise AppError(code="forbidden", message="You do not have access to this resource.", status_code=403)
        return current_user

    return dependency
