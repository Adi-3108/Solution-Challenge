from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, Float, ForeignKey, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import ORMBaseModel
from app.models.enums import AuditRunStatus, NotificationType, SeverityLevel


class AuditRun(ORMBaseModel):
    __tablename__ = "audit_runs"

    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"))
    dataset_id: Mapped[str] = mapped_column(ForeignKey("datasets.id", ondelete="CASCADE"))
    model_id: Mapped[str | None] = mapped_column(
        ForeignKey("model_artifacts.id", ondelete="SET NULL"), nullable=True
    )
    status: Mapped[AuditRunStatus] = mapped_column(
        Enum(AuditRunStatus, name="audit_run_status"),
        default=AuditRunStatus.QUEUED,
        nullable=False,
    )
    bias_risk_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    stage_label: Mapped[str] = mapped_column(
        String(255), nullable=False, default="Queued for analysis..."
    )
    thresholds_json: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False, default=dict)
    summary_json: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False, default=dict)
    shap_json: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False, default=dict)
    proxy_matrix_json: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False, default=dict)
    distributions_json: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False, default=dict)
    remediation_json: Mapped[list[dict[str, object]]] = mapped_column(JSON, nullable=False, default=list)

    project = relationship("Project", back_populates="audit_runs")
    dataset = relationship("Dataset", back_populates="audit_runs")
    model = relationship("ModelArtifact", back_populates="audit_runs")
    results = relationship("AuditResult", back_populates="run")
    reports = relationship("Report", back_populates="run")


class AuditResult(ORMBaseModel):
    __tablename__ = "audit_results"

    run_id: Mapped[str] = mapped_column(ForeignKey("audit_runs.id", ondelete="CASCADE"))
    metric_name: Mapped[str] = mapped_column(String(255), nullable=False)
    group_name: Mapped[str] = mapped_column(String(255), nullable=False)
    intersectional_groups: Mapped[dict[str, str]] = mapped_column(JSON, nullable=False, default=dict)
    value: Mapped[float] = mapped_column(Float, nullable=False)
    severity: Mapped[SeverityLevel] = mapped_column(
        Enum(SeverityLevel, name="severity_level"), nullable=False
    )
    threshold_used: Mapped[float] = mapped_column(Float, nullable=False)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    details_json: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False, default=dict)

    run = relationship("AuditRun", back_populates="results")


class AuditLog(ORMBaseModel):
    __tablename__ = "audit_logs"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    action: Mapped[str] = mapped_column(String(255), nullable=False)
    resource_type: Mapped[str] = mapped_column(String(255), nullable=False)
    resource_id: Mapped[str] = mapped_column(String(255), nullable=False)
    metadata_json: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    user = relationship("User", back_populates="audit_logs")


class Notification(ORMBaseModel):
    __tablename__ = "notifications"

    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"))
    type: Mapped[NotificationType] = mapped_column(
        Enum(NotificationType, name="notification_type"), nullable=False
    )
    destination: Mapped[str] = mapped_column(String(500), nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    project = relationship("Project", back_populates="notifications")

