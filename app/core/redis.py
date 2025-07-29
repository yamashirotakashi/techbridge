"""Redis configuration and connection management."""

import redis.asyncio as redis
from redis.asyncio import Redis

from app.core.config import settings

# Global Redis connection pool
redis_pool: Redis | None = None


async def get_redis() -> Redis:
    """Get Redis connection."""
    global redis_pool
    
    if redis_pool is None:
        redis_pool = redis.from_url(
            str(settings.REDIS_URL),
            decode_responses=True,
        )
    
    return redis_pool


async def close_redis() -> None:
    """Close Redis connection pool."""
    global redis_pool
    
    if redis_pool is not None:
        await redis_pool.close()
        redis_pool = None