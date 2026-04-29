from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        enable_decoding=False,
    )

    api_prefix: str = "/api/v1"
    project_name: str = "FairSight"
    environment: str = "development"
    secret_key: str = Field(alias="SECRET_KEY")
    access_token_expire_minutes: int = Field(default=30, alias="ACCESS_TOKEN_EXPIRE_MINUTES")
    refresh_token_expire_days: int = Field(default=14, alias="REFRESH_TOKEN_EXPIRE_DAYS")
    reset_token_expire_minutes: int = Field(default=30, alias="RESET_TOKEN_EXPIRE_MINUTES")
    database_url: str = Field(alias="DATABASE_URL")
    alembic_database_url: str = Field(alias="ALEMBIC_DATABASE_URL")
    redis_url: str = Field(alias="REDIS_URL")
    cors_origins: list[str] = Field(default_factory=list, alias="CORS_ORIGINS")
    frontend_origin: str = Field(default="http://localhost", alias="FRONTEND_ORIGIN")
    smtp_host: str = Field(default="localhost", alias="SMTP_HOST")
    smtp_port: int = Field(default=25, alias="SMTP_PORT")
    smtp_user: str | None = Field(default=None, alias="SMTP_USER")
    smtp_pass: str | None = Field(default=None, alias="SMTP_PASS")
    smtp_from: str = Field(default="noreply@fairsight.local", alias="SMTP_FROM")
    file_storage_path: Path = Field(default=Path("/app/uploads"), alias="FILE_STORAGE_PATH")
    pdf_report_path: Path = Field(default=Path("/app/uploads/reports"), alias="PDF_REPORT_PATH")
    max_file_size_mb: int = Field(default=200, alias="MAX_FILE_SIZE_MB")
    allowed_file_retention_days: int = Field(default=30, alias="ALLOWED_FILE_RETENTION_DAYS")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    webhook_timeout_seconds: int = Field(default=5, alias="WEBHOOK_TIMEOUT_SECONDS")
    rate_limit_per_minute: int = Field(default=100, alias="RATE_LIMIT_PER_MINUTE")
    celery_task_always_eager: bool = Field(default=False, alias="CELERY_TASK_ALWAYS_EAGER")
    s3_endpoint: str | None = Field(default=None, alias="S3_ENDPOINT")
    s3_access_key: str | None = Field(default=None, alias="S3_ACCESS_KEY")
    s3_secret_key: str | None = Field(default=None, alias="S3_SECRET_KEY")
    s3_bucket: str | None = Field(default=None, alias="S3_BUCKET")
    google_client_id: str | None = Field(default=None, alias="GOOGLE_CLIENT_ID")
    google_client_secret: str | None = Field(default=None, alias="GOOGLE_CLIENT_SECRET")
    gemini_api_key: str | None = Field(default=None, alias="GEMINI_API_KEY")
    gemini_model: str = Field(default="gemini-1.5-flash", alias="GEMINI_MODEL")
    gemini_timeout_seconds: int = Field(default=25, alias="GEMINI_TIMEOUT_SECONDS")

    @field_validator("cors_origins", mode="before")
    @classmethod
    def split_cors_origins(cls, value: str | list[str]) -> list[str]:
        if isinstance(value, list):
            return value
        # Support both JSON-like lists and comma-separated values in .env.
        if isinstance(value, str) and value.strip().startswith("[") and value.strip().endswith("]"):
            stripped = value.strip()[1:-1]
            return [item.strip().strip("'\"") for item in stripped.split(",") if item.strip()]
        return [item.strip() for item in value.split(",") if item.strip()]

    @field_validator("database_url", mode="before")
    @classmethod
    def normalize_database_url(cls, value: str) -> str:
        """
        Render's `connectionString` for Postgres is typically `postgresql://...`.
        This app expects asyncpg for the async SQLAlchemy engine.
        """
        if not value:
            return value
        if value.startswith("postgres://") and "+asyncpg" not in value:
            return value.replace("postgres://", "postgresql+asyncpg://", 1)
        if value.startswith("postgresql://") and "+asyncpg" not in value:
            return value.replace("postgresql://", "postgresql+asyncpg://", 1)
        return value

    @field_validator("alembic_database_url", mode="before")
    @classmethod
    def normalize_alembic_database_url(cls, value: str) -> str:
        """
        Alembic env expects a sync SQLAlchemy URL with psycopg.
        """
        if not value:
            return value
        if value.startswith("postgres://") and "+psycopg" not in value:
            return value.replace("postgres://", "postgresql+psycopg://", 1)
        if value.startswith("postgresql://") and "+psycopg" not in value:
            return value.replace("postgresql://", "postgresql+psycopg://", 1)
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

