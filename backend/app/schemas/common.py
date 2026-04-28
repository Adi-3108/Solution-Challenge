from __future__ import annotations

from datetime import datetime
from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict

PayloadT = TypeVar("PayloadT")


class MetaResponse(BaseModel):
    request_id: str
    next_cursor: str | None = None


class Envelope(BaseModel, Generic[PayloadT]):
    data: PayloadT
    meta: MetaResponse


class ErrorBody(BaseModel):
    code: str
    message: str
    details: dict[str, object] = {}


class ErrorEnvelope(BaseModel):
    error: ErrorBody


class CursorPage(BaseModel):
    next_cursor: str | None = None


class TimestampedModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str


class AuditTrailItem(BaseModel):
    created_at: datetime
    action: str
    resource_type: str
    resource_id: str

