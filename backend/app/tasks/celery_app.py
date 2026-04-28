from __future__ import annotations

from celery import Celery

from app.core.config import settings

celery_app = Celery(
    "fairsight",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["app.tasks.run_audit"],
)
celery_app.conf.update(
    task_always_eager=settings.celery_task_always_eager,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_default_retry_delay=5,
)

# Import task modules so decorators register tasks when the worker boots.
import app.tasks.run_audit  # noqa: E402,F401
