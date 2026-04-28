from __future__ import annotations

from enum import StrEnum


class UserRole(StrEnum):
    ADMIN = "admin"
    ANALYST = "analyst"
    VIEWER = "viewer"


class AuditRunStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class SeverityLevel(StrEnum):
    GREEN = "green"
    AMBER = "amber"
    RED = "red"


class ReportFormat(StrEnum):
    PDF = "pdf"
    JSON = "json"


class NotificationType(StrEnum):
    EMAIL = "email"
    WEBHOOK = "webhook"


class ModelType(StrEnum):
    PICKLE = "pkl"
    JOBLIB = "joblib"
    ONNX = "onnx"

