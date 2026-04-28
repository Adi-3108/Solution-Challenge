from __future__ import annotations

from enum import StrEnum
from typing import Any, TypeVar

from sqlalchemy import Enum as SQLAlchemyEnum
from sqlalchemy import String
from sqlalchemy.types import TypeDecorator


EnumT = TypeVar("EnumT", bound=StrEnum)


class ValueBackedEnum(TypeDecorator):
    impl = String
    cache_ok = True

    def __init__(self, enum_cls: type[EnumT], name: str):
        self.enum_cls = enum_cls
        self.name = name
        self._enum_impl = SQLAlchemyEnum(
            *[member.value for member in enum_cls],
            name=name,
            validate_strings=True,
        )
        super().__init__()

    def load_dialect_impl(self, dialect: Any) -> SQLAlchemyEnum:
        return dialect.type_descriptor(self._enum_impl)

    def process_bind_param(self, value: EnumT | str | None, dialect: Any) -> str | None:
        if value is None:
            return None
        if isinstance(value, self.enum_cls):
            return value.value
        if isinstance(value, str):
            return self.enum_cls(value).value
        raise TypeError(f"Unsupported {self.enum_cls.__name__} value: {value!r}")

    def process_result_value(self, value: str | None, dialect: Any) -> EnumT | None:
        if value is None:
            return None
        return self.enum_cls(value)

    def copy(self, **kw: Any) -> ValueBackedEnum:
        return ValueBackedEnum(self.enum_cls, self.name)


def db_enum(enum_cls: type[EnumT], name: str) -> ValueBackedEnum:
    return ValueBackedEnum(enum_cls, name)


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
