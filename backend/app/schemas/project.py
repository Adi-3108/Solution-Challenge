from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.models.enums import AuditRunStatus


class ProjectCreate(BaseModel):
    name: str = Field(min_length=3, max_length=255)
    description: str | None = Field(default=None, max_length=2000)


class ProjectUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=3, max_length=255)
    description: str | None = Field(default=None, max_length=2000)
    archived_at: datetime | None = None


class ProjectSummary(BaseModel):
    id: str
    name: str
    description: str | None
    created_at: datetime
    archived_at: datetime | None
    last_run_date: datetime | None = None
    last_run_status: AuditRunStatus | None = None
    risk_score: float | None = None
    run_count: int = 0

    model_config = {"from_attributes": True}


class ProjectDetail(ProjectSummary):
    datasets: list[dict[str, object]] = []
    models: list[dict[str, object]] = []
    runs: list[dict[str, object]] = []

