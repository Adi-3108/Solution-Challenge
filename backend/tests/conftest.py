from __future__ import annotations

from collections.abc import AsyncIterator
import os
from pathlib import Path
import shutil
from uuid import uuid4

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./tests.db")
os.environ.setdefault("ALEMBIC_DATABASE_URL", "sqlite:///./tests.db")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/15")
os.environ.setdefault("FILE_STORAGE_PATH", "./backend/tests/tmp_uploads")
os.environ.setdefault("PDF_REPORT_PATH", "./backend/tests/tmp_uploads/reports")
os.environ.setdefault("CORS_ORIGINS", '["http://localhost:5173"]')

from app.core.database import Base, get_db_session
from app.main import app


class FakeRedis:
    def __init__(self) -> None:
        self.store: dict[str, str] = {}

    async def incr(self, key: str) -> int:
        current = int(self.store.get(key, "0")) + 1
        self.store[key] = str(current)
        return current

    async def expire(self, key: str, _: int) -> bool:
        return key in self.store

    async def get(self, key: str) -> str | None:
        return self.store.get(key)

    async def setex(self, key: str, _: int, value: str) -> bool:
        self.store[key] = value
        return True

    async def ping(self) -> bool:
        return True

    async def exists(self, key: str) -> int:
        return int(key in self.store)


@pytest_asyncio.fixture
async def client(monkeypatch: pytest.MonkeyPatch) -> AsyncIterator[AsyncClient]:
    runtime_root = Path(__file__).resolve().parent / ".runtime" / str(uuid4())
    runtime_root.mkdir(parents=True, exist_ok=True)
    database_url = f"sqlite+aiosqlite:///{runtime_root / 'test.db'}"
    engine = create_async_engine(database_url, future=True)
    test_session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    async def override_db() -> AsyncIterator[AsyncSession]:
        async with test_session() as session:
            yield session

    app.dependency_overrides[get_db_session] = override_db

    from app.core import database as database_module
    from app.core import rate_limit as rate_limit_module
    from app.core import redis as redis_module
    from app.services.auth import service as auth_service_module
    from app.services.audit import service as audit_service_module
    from app.services.storage import service as storage_module
    from app.tasks.celery_app import celery_app

    fake_redis = FakeRedis()
    monkeypatch.setattr(database_module, "SessionLocal", test_session)
    monkeypatch.setattr(redis_module, "get_redis_client", lambda: fake_redis)
    monkeypatch.setattr(rate_limit_module, "get_redis_client", lambda: fake_redis)
    monkeypatch.setattr(auth_service_module, "get_redis_client", lambda: fake_redis)
    monkeypatch.setattr(audit_service_module, "get_redis_client", lambda: fake_redis)
    storage_module.storage_service = storage_module.LocalStorageService()
    storage_module.storage_service.base_path = runtime_root / "uploads"
    storage_module.storage_service.base_path.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr("app.api.v1.routes.datasets.storage_service", storage_module.storage_service)
    monkeypatch.setattr("app.api.v1.routes.models.storage_service", storage_module.storage_service)
    monkeypatch.setattr("app.services.audit.service.storage_service", storage_module.storage_service)
    monkeypatch.setattr(celery_app.conf, "task_always_eager", True)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as async_client:
        yield async_client

    app.dependency_overrides.clear()
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)
    await engine.dispose()
    shutil.rmtree(runtime_root, ignore_errors=True)


@pytest.fixture
def fixtures_path() -> Path:
    return Path(__file__).resolve().parent / "fixtures"
