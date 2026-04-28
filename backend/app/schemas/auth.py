from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.models.enums import UserRole

MAX_BCRYPT_PASSWORD_BYTES = 72


def _validate_bcrypt_password_length(password: str) -> str:
    if len(password.encode("utf-8")) > MAX_BCRYPT_PASSWORD_BYTES:
        raise ValueError(f"Password must be at most {MAX_BCRYPT_PASSWORD_BYTES} bytes.")
    return password


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    role: UserRole = UserRole.ANALYST

    @field_validator("password")
    @classmethod
    def validate_password_length_for_bcrypt(cls, value: str) -> str:
        return _validate_bcrypt_password_length(value)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)

    @field_validator("password")
    @classmethod
    def validate_password_length_for_bcrypt(cls, value: str) -> str:
        return _validate_bcrypt_password_length(value)


class RefreshRequest(BaseModel):
    refresh_token: str | None = None


class ResetPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordConfirm(BaseModel):
    token: str
    new_password: str = Field(min_length=8, max_length=128)

    @field_validator("new_password")
    @classmethod
    def validate_new_password_length_for_bcrypt(cls, value: str) -> str:
        return _validate_bcrypt_password_length(value)


class UserResponse(BaseModel):
    id: str
    email: EmailStr
    role: UserRole
    created_at: datetime

    model_config = {"from_attributes": True}


class AuthTokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    user: UserResponse

