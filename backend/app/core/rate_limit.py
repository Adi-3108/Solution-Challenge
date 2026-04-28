from __future__ import annotations

from fastapi import Request

from app.core.config import settings
from app.core.errors import AppError
from app.core.redis import get_redis_client


async def enforce_user_rate_limit(request: Request, bucket: str) -> None:
    user_id = getattr(request.state, "user_id", "anonymous")
    key = f"ratelimit:{bucket}:{user_id}"
    client = get_redis_client()
    current = await client.incr(key)
    if current == 1:
        await client.expire(key, 60)
    if current > settings.rate_limit_per_minute:
        raise AppError(
            code="rate_limit_exceeded",
            message="Too many audit requests. Please try again in a minute.",
            status_code=429,
        )

