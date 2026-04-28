from __future__ import annotations

from datetime import UTC, datetime, timedelta
from enum import StrEnum

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings


class TokenType(StrEnum):
    ACCESS = "access"
    REFRESH = "refresh"
    RESET = "reset"


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
ALGORITHM = "HS256"
ACCESS_COOKIE_NAME = "fairsight_access_token"
REFRESH_COOKIE_NAME = "fairsight_refresh_token"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def create_token(subject: str, token_type: TokenType, expires_delta: timedelta) -> str:
    expires_at = datetime.now(UTC) + expires_delta
    payload = {"sub": subject, "type": token_type.value, "exp": expires_at}
    return jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM)


def create_access_token(subject: str) -> str:
    expiry = timedelta(minutes=settings.access_token_expire_minutes)
    return create_token(subject, TokenType.ACCESS, expiry)


def create_refresh_token(subject: str) -> str:
    expiry = timedelta(days=settings.refresh_token_expire_days)
    return create_token(subject, TokenType.REFRESH, expiry)


def create_reset_token(subject: str) -> str:
    expiry = timedelta(minutes=settings.reset_token_expire_minutes)
    return create_token(subject, TokenType.RESET, expiry)


def decode_token(token: str, expected_type: TokenType) -> str:
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
    except JWTError as exc:
        raise ValueError("Invalid token") from exc
    if payload.get("type") != expected_type.value:
        raise ValueError("Unexpected token type")
    subject = payload.get("sub")
    if not subject:
        raise ValueError("Token subject missing")
    return str(subject)

