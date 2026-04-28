from __future__ import annotations

import asyncio

from app.core.database import engine
from app.services.audit.service import execute_audit_run
from app.tasks.celery_app import celery_app


@celery_app.task(bind=True, max_retries=3)
def run_audit_task(self, run_id: str, request_id: str) -> None:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(execute_audit_run(run_id, request_id))
    except Exception as exc:
        loop.run_until_complete(engine.dispose())
        raise self.retry(exc=exc, countdown=5 * (self.request.retries + 1))
    finally:
        if not loop.is_closed():
            loop.run_until_complete(engine.dispose())
            loop.close()
        asyncio.set_event_loop(None)
