from __future__ import annotations

from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db_session
from app.core.errors import AppError
from app.core.security import REFRESH_COOKIE_NAME, TokenType, decode_token, hash_password
from app.models.user import User
from app.schemas.auth import (
    GoogleLoginRequest,
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    ResetPasswordConfirm,
    ResetPasswordRequest,
)
from app.services.auth.service import (
    attach_auth_cookies,
    authenticate_user,
    build_auth_response,
    build_reset_token,
    clear_auth_cookies,
    ensure_refresh_token_active,
    google_login_or_register,
    register_user,
    revoke_refresh_token,
)
from app.services.notifications.service import send_password_reset_email
from app.utils.audit_log import create_audit_log
from app.utils.response import envelope

router = APIRouter()


@router.post("/register")
async def register(
    payload: RegisterRequest,
    request: Request,
    response: Response,
    session: AsyncSession = Depends(get_db_session),
):
    user = await register_user(session, payload.email, payload.password, payload.role)
    auth = build_auth_response(user)
    attach_auth_cookies(response, auth.access_token, auth.refresh_token)
    await create_audit_log(session, user.id, "register", "user", user.id, {})
    await session.commit()
    return envelope(request, auth.model_dump(mode="json"))


@router.post("/login")
async def login(
    payload: LoginRequest,
    request: Request,
    response: Response,
    session: AsyncSession = Depends(get_db_session),
):
    user = await authenticate_user(session, payload.email, payload.password)
    auth = build_auth_response(user)
    attach_auth_cookies(response, auth.access_token, auth.refresh_token)
    await create_audit_log(session, user.id, "login", "user", user.id, {})
    await session.commit()
    return envelope(request, auth.model_dump(mode="json"))


@router.post("/google")
async def google_login(
    payload: GoogleLoginRequest,
    request: Request,
    response: Response,
    session: AsyncSession = Depends(get_db_session),
):
    user = await google_login_or_register(session, payload.credential)
    auth = build_auth_response(user)
    attach_auth_cookies(response, auth.access_token, auth.refresh_token)
    await create_audit_log(session, user.id, "google_login", "user", user.id, {})
    await session.commit()
    return envelope(request, auth.model_dump(mode="json"))


@router.post("/refresh")
async def refresh_token(
    request: Request,
    response: Response,
    payload: RefreshRequest | None = None,
    session: AsyncSession = Depends(get_db_session),
):
    refresh_token = payload.refresh_token if payload and payload.refresh_token else request.cookies.get(REFRESH_COOKIE_NAME)
    if not refresh_token:
        raise AppError(code="invalid_token", message="Refresh token missing.", status_code=401)
    email = await ensure_refresh_token_active(refresh_token)
    user = (await session.execute(select(User).where(User.email == email, User.deleted_at.is_(None)))).scalar_one_or_none()
    if user is None:
        raise AppError(code="invalid_token", message="Refresh token is invalid.", status_code=401)
    auth = build_auth_response(user)
    attach_auth_cookies(response, auth.access_token, auth.refresh_token)
    return envelope(request, auth.model_dump(mode="json"))


@router.post("/logout")
async def logout(
    request: Request,
    response: Response,
    payload: RefreshRequest | None = None,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    refresh_token = payload.refresh_token if payload and payload.refresh_token else request.cookies.get(REFRESH_COOKIE_NAME)
    if refresh_token:
        await revoke_refresh_token(refresh_token)
    clear_auth_cookies(response)
    await create_audit_log(session, current_user.id, "logout", "user", current_user.id, {})
    await session.commit()
    return envelope(request, {"success": True})


@router.get("/me")
async def me(request: Request, current_user: User = Depends(get_current_user)):
    return envelope(
        request,
        {
            "id": current_user.id,
            "email": current_user.email,
            "role": current_user.role.value,
            "created_at": current_user.created_at.isoformat(),
        },
    )


@router.post("/reset-password/request")
async def reset_password_request(
    payload: ResetPasswordRequest,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
):
    user = (await session.execute(select(User).where(User.email == payload.email, User.deleted_at.is_(None)))).scalar_one_or_none()
    if user:
        token = build_reset_token(user.email)
        await send_password_reset_email(user.email, token)
    return envelope(request, {"message": "If the account exists, a reset email has been sent."})


@router.post("/reset-password/confirm")
async def reset_password_confirm(
    payload: ResetPasswordConfirm,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
):
    try:
        email = decode_token(payload.token, TokenType.RESET)
    except ValueError as exc:
        raise AppError(code="invalid_token", message="Reset token is invalid.", status_code=400) from exc
    user = (await session.execute(select(User).where(User.email == email, User.deleted_at.is_(None)))).scalar_one_or_none()
    if user is None:
        raise AppError(code="invalid_token", message="Reset token is invalid.", status_code=400)
    user.hashed_password = hash_password(payload.new_password)
    await create_audit_log(session, user.id, "reset_password", "user", user.id, {})
    await session.commit()
    return envelope(request, {"success": True})
