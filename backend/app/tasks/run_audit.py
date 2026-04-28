from __future__ import annotations

import asyncio

from app.services.audit.service import execute_audit_run
from app.tasks.celery_app import celery_app


@celery_app.task(bind=True, max_retries=3)
def run_audit_task(self, run_id: str, request_id: str) -> None:
    try:
        asyncio.run(execute_audit_run(run_id, request_id))
    except Exception as exc:
        raise self.retry(exc=exc, countdown=5 * (self.request.retries + 1))

