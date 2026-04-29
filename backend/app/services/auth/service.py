from __future__ import annotations

from google.oauth2 import id_token as google_id_token
from google.auth.transport import requests as google_requests
from fastapi import Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.errors import AppError
from app.core.redis import get_redis_client
from app.core.security import (
    ACCESS_COOKIE_NAME,
    REFRESH_COOKIE_NAME,
    TokenType,
    create_access_token,
    create_refresh_token,
    create_reset_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.auth import AuthTokenResponse


async def register_user(
    session: AsyncSession, email: str, password: str, role: UserRole
) -> User:
    existing = await session.execute(select(User).where(User.email == email))
    if existing.scalar_one_or_none():
        raise AppError(code="email_exists", message="An account with that email already exists.", status_code=409)
    safe_role = UserRole.ANALYST if role == UserRole.ADMIN else role
    user = User(email=email, hashed_password=hash_password(password), role=safe_role)
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


async def authenticate_user(session: AsyncSession, email: str, password: str) -> User:
    result = await session.execute(select(User).where(User.email == email, User.deleted_at.is_(None)))
    user = result.scalar_one_or_none()
    if not user or not verify_password(password, user.hashed_password):
        raise AppError(code="invalid_credentials", message="Invalid email or password.", status_code=401)
    return user


def build_auth_response(user: User) -> AuthTokenResponse:
    access_token = create_access_token(user.email)
    refresh_token = create_refresh_token(user.email)
    return AuthTokenResponse(access_token=access_token, refresh_token=refresh_token, user=user)


def attach_auth_cookies(response: Response, access_token: str, refresh_token: str) -> None:
    secure_cookie = settings.environment != "development"
    # Cross-site frontend/backend deployments (e.g. Vercel + Render) require
    # SameSite=None with Secure cookies so browsers include auth cookies on XHR.
    same_site = "none" if secure_cookie else "lax"
    response.set_cookie(
        ACCESS_COOKIE_NAME,
        access_token,
        httponly=True,
        secure=secure_cookie,
        samesite=same_site,
        max_age=60 * 60,
    )
    response.set_cookie(
        REFRESH_COOKIE_NAME,
        refresh_token,
        httponly=True,
        secure=secure_cookie,
        samesite=same_site,
        max_age=60 * 60 * 24 * 14,
    )


def clear_auth_cookies(response: Response) -> None:
    response.delete_cookie(ACCESS_COOKIE_NAME)
    response.delete_cookie(REFRESH_COOKIE_NAME)


async def revoke_refresh_token(token: str) -> None:
    await get_redis_client().setex(f"revoked-refresh:{token}", 60 * 60 * 24 * 14, "1")


async def ensure_refresh_token_active(token: str) -> str:
    if await get_redis_client().exists(f"revoked-refresh:{token}"):
        raise AppError(code="invalid_token", message="Refresh token is no longer valid.", status_code=401)
    try:
        return decode_token(token, TokenType.REFRESH)
    except ValueError as exc:
        raise AppError(code="invalid_token", message="Refresh token is invalid.", status_code=401) from exc


def build_reset_token(email: str) -> str:
    return create_reset_token(email)


async def google_login_or_register(session: AsyncSession, credential: str) -> "User":
    """Verify a Google ID token and return (or create) the matching FairSight user."""
    if not settings.google_client_id:
        raise AppError(
            code="google_auth_disabled",
            message="Google authentication is not configured on this server.",
            status_code=501,
        )
    try:
        id_info = google_id_token.verify_oauth2_token(
            credential,
            google_requests.Request(),
            settings.google_client_id,
        )
    except ValueError as exc:
        raise AppError(
            code="invalid_google_token",
            message="Google ID token is invalid or expired.",
            status_code=401,
        ) from exc

    google_sub: str = id_info["sub"]  # stable, unique Google account identifier
    email: str = id_info.get("email", "")

    # 1. Look up by stable google_id
    result = await session.execute(select(User).where(User.google_id == google_sub, User.deleted_at.is_(None)))
    user = result.scalar_one_or_none()
    if user:
        return user

    # 2. Account exists with same email (created via password) — link google_id
    result = await session.execute(select(User).where(User.email == email, User.deleted_at.is_(None)))
    user = result.scalar_one_or_none()
    if user:
        user.google_id = google_sub
        await session.commit()
        await session.refresh(user)
        return user

    # 3. Brand-new Google user — create account (no password)
    user = User(
        email=email,
        hashed_password=None,
        google_id=google_sub,
        role=UserRole.ANALYST,
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user
