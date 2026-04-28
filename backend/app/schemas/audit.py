from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.models.enums import AuditRunStatus, SeverityLevel
from app.services.bias_engine.schemas import BiasThresholdConfig


class RunCreateRequest(BaseModel):
    dataset_id: str
    model_id: str | None = None
    thresholds: BiasThresholdConfig = Field(default_factory=BiasThresholdConfig)


class RunSummaryResponse(BaseModel):
    id: str
    project_id: str
    dataset_id: str
    model_id: str | None
    status: AuditRunStatus
    bias_risk_score: float | None
    started_at: datetime | None
    completed_at: datetime | None
    error_message: str | None
    stage_label: str
    summary: dict[str, object]


class AuditResultResponse(BaseModel):
    id: str
    metric_name: str
    group_name: str
    intersectional_groups: dict[str, str]
    value: float
    severity: SeverityLevel
    threshold_used: float
    explanation: str
    details_json: dict[str, object]

    model_config = {"from_attributes": True}


class ReportCreateRequest(BaseModel):
    format: str = Field(pattern="^(pdf|json)$")

