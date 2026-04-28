from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import ORMBaseModel, CreatedTimestampMixin
from app.models.enums import UserRole, db_enum


class User(ORMBaseModel, CreatedTimestampMixin):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        db_enum(UserRole, "user_role"), default=UserRole.VIEWER, nullable=False
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    projects = relationship("Project", back_populates="user")
    audit_logs = relationship("AuditLog", back_populates="user")
