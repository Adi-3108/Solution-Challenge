from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import ORMBaseModel, CreatedTimestampMixin


class Project(ORMBaseModel, CreatedTimestampMixin):
    __tablename__ = "projects"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user = relationship("User", back_populates="projects")
    datasets = relationship("Dataset", back_populates="project")
    models = relationship("ModelArtifact", back_populates="project")
    audit_runs = relationship("AuditRun", back_populates="project")
    notifications = relationship("Notification", back_populates="project")

