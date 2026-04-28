from __future__ import annotations

import base64
from datetime import datetime


def encode_cursor(created_at: datetime, entity_id: str) -> str:
    payload = f"{created_at.isoformat()}|{entity_id}"
    return base64.urlsafe_b64encode(payload.encode("utf-8")).decode("utf-8")


def decode_cursor(cursor: str) -> tuple[datetime, str]:
    raw = base64.urlsafe_b64decode(cursor.encode("utf-8")).decode("utf-8")
    created_at, entity_id = raw.split("|", maxsplit=1)
    return datetime.fromisoformat(created_at), entity_id

