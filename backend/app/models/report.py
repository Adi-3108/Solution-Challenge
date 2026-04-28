from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import ORMBaseModel
from app.models.enums import ReportFormat, db_enum


class Report(ORMBaseModel):
    __tablename__ = "reports"

    run_id: Mapped[str] = mapped_column(ForeignKey("audit_runs.id", ondelete="CASCADE"))
    format: Mapped[ReportFormat] = mapped_column(
        db_enum(ReportFormat, "report_format"), nullable=False
    )
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    file_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    run = relationship("AuditRun", back_populates="reports")
