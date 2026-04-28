from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from app.models.enums import UserRole


class UserAdminResponse(BaseModel):
    id: str
    email: str
    role: UserRole
    created_at: datetime
    deleted_at: datetime | None

    model_config = {"from_attributes": True}


class UserRoleUpdateRequest(BaseModel):
    role: UserRole

