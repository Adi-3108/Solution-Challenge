from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import ORMBaseModel
from app.models.enums import ModelType


class Dataset(ORMBaseModel):
    __tablename__ = "datasets"

    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"))
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    file_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    row_count: Mapped[int] = mapped_column(Integer, nullable=False)
    col_count: Mapped[int] = mapped_column(Integer, nullable=False)
    target_column: Mapped[str] = mapped_column(String(255), nullable=False)
    protected_columns: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    positive_label: Mapped[str] = mapped_column(String(255), nullable=False)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    column_types: Mapped[dict[str, str]] = mapped_column(JSON, nullable=False, default=dict)
    prediction_column: Mapped[str | None] = mapped_column(String(255), nullable=True)
    score_column: Mapped[str | None] = mapped_column(String(255), nullable=True)

    project = relationship("Project", back_populates="datasets")
    audit_runs = relationship("AuditRun", back_populates="dataset")


class ModelArtifact(ORMBaseModel):
    __tablename__ = "model_artifacts"

    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"))
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    file_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    model_type: Mapped[ModelType] = mapped_column(
        Enum(ModelType, name="model_type"), nullable=False
    )
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    project = relationship("Project", back_populates="models")
    audit_runs = relationship("AuditRun", back_populates="model")
