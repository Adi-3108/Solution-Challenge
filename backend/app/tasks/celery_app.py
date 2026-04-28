from __future__ import annotations

from celery import Celery

from app.core.config import settings

celery_app = Celery("fairsight", broker=settings.redis_url, backend=settings.redis_url)
celery_app.conf.update(
    task_always_eager=settings.celery_task_always_eager,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_default_retry_delay=5,
)

