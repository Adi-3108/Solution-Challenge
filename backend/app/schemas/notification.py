from __future__ import annotations

from pydantic import BaseModel, Field

from app.models.enums import NotificationType


class NotificationResponse(BaseModel):
    id: str
    project_id: str
    type: NotificationType
    destination: str
    enabled: bool

    model_config = {"from_attributes": True}


class NotificationUpdateItem(BaseModel):
    type: NotificationType
    destination: str = Field(min_length=3, max_length=500)
    enabled: bool = True


class NotificationUpdateRequest(BaseModel):
    notifications: list[NotificationUpdateItem]

