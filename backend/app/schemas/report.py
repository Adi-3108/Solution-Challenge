from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from app.models.enums import ReportFormat


class ReportResponse(BaseModel):
    id: str
    run_id: str
    format: ReportFormat
    file_hash: str
    generated_at: datetime

    model_config = {"from_attributes": True}

