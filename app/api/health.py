"""Health check endpoints."""

from typing import Dict

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.redis import get_redis

router = APIRouter()


@router.get("/")
async def health_check() -> Dict[str, str]:
    """Basic health check."""
    return {"status": "healthy"}


@router.get("/ready")
async def readiness_check(
    db: AsyncSession = Depends(get_db),
) -> Dict[str, str]:
    """Readiness check with database and Redis connectivity."""
    # Check database
    try:
        await db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)}"

    # Check Redis
    try:
        redis = await get_redis()
        await redis.ping()
        redis_status = "connected"
    except Exception as e:
        redis_status = f"error: {str(e)}"

    status = "ready" if db_status == "connected" and redis_status == "connected" else "not_ready"

    return {
        "status": status,
        "database": db_status,
        "redis": redis_status,
    }