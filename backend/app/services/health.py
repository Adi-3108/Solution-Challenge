from __future__ import annotations

import asyncio

from sqlalchemy import text

from app.core.config import settings
from app.core.database import engine
from app.core.redis import get_redis_client
from app.tasks.celery_app import celery_app


async def health_status() -> dict[str, object]:
    database_ok = await _database_health()
    redis_ok = await _redis_health()
    worker_count = await asyncio.to_thread(_celery_worker_count)
    worker_ok = settings.celery_task_always_eager or worker_count > 0
    return {
        "status": "ok" if database_ok and redis_ok and worker_ok else "degraded",
        "checks": {
            "database": database_ok,
            "redis": redis_ok,
            "worker": worker_ok,
            "celery_worker_count": worker_count,
        },
    }


async def _database_health() -> bool:
    try:
        async with engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


async def _redis_health() -> bool:
    try:
        return bool(await get_redis_client().ping())
    except Exception:
        return False


def _celery_worker_count() -> int:
    try:
        inspection = celery_app.control.inspect(timeout=1)
        stats = inspection.stats() or {}
        return len(stats.keys())
    except Exception:
        return 0
