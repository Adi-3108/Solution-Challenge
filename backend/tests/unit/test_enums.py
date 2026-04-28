from __future__ import annotations

from sqlalchemy.dialects import postgresql

from app.models.enums import UserRole, db_enum


def test_db_enum_binds_enum_members_to_lowercase_values() -> None:
    role_type = db_enum(UserRole, "user_role")
    processor = role_type.bind_processor(postgresql.dialect())
    assert processor is not None
    assert processor(UserRole.ANALYST) == "analyst"
    assert processor(UserRole.VIEWER) == "viewer"


def test_db_enum_rehydrates_enum_members_from_database_values() -> None:
    role_type = db_enum(UserRole, "user_role")
    processor = role_type.result_processor(postgresql.dialect(), None)
    assert processor is not None
    assert processor("analyst") == UserRole.ANALYST
    assert processor("viewer") == UserRole.VIEWER
