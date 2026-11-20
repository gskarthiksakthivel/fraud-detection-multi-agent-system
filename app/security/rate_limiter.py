"""
rate_limiter.py
===============
LAYER: Security — Rate Limiting

Sliding window rate limiter using Redis.
Prevents agent flooding and token cost explosion.
Default: 60 requests per minute per client IP.
"""

import time
import logging
from fastapi import Request, HTTPException, status
import redis.asyncio as redis
from app.config import settings

logger = logging.getLogger(__name__)
_redis_client = None


async def get_redis():
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.from_url(settings.redis_url, encoding="utf-8", decode_responses=True)
    return _redis_client


async def rate_limit_middleware(request: Request, call_next):
    """FastAPI middleware for sliding window rate limiting."""
    client_ip = request.client.host if request.client else "unknown"
    key = f"rate_limit:{client_ip}"

    try:
        r = await get_redis()
        now = time.time()
        window_start = now - 60  # 60-second window

        pipe = r.pipeline()
        await pipe.zremrangebyscore(key, 0, window_start)
        await pipe.zadd(key, {str(now): now})
        await pipe.zcard(key)
        await pipe.expire(key, 60)
        results = await pipe.execute()

        request_count = results[2]
        if request_count > settings.rate_limit_per_minute:
            logger.warning(f"[RATE_LIMITER] Rate limit exceeded for {client_ip}: {request_count} req/min")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. Max {settings.rate_limit_per_minute} requests per minute."
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.warning(f"[RATE_LIMITER] Redis unavailable, skipping rate limit: {e}")

    return await call_next(request)
