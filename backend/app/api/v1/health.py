"""
Manufacturing Decision Copilot - Health Check API
GET /api/v1/health
GET /api/v1/version
"""
import redis.asyncio as aioredis
from fastapi import APIRouter

from app.core.config import settings
from app.core.logging import get_logger
from app.database.chroma import check_chroma_health
from app.database.session import check_db_health

logger = get_logger(__name__)
router = APIRouter(tags=["System"])


async def check_redis_health() -> bool:
    """Returns True if Redis is reachable."""
    try:
        client = aioredis.from_url(settings.redis_url, decode_responses=True)
        await client.ping()
        await client.aclose()
        return True
    except Exception as exc:
        logger.warning("Redis health check failed", error=str(exc))
        return False


@router.get("/health")
async def health_check() -> dict:
    """
    System health check.
    Returns the status of all dependent services.
    """
    db_ok = await check_db_health()
    redis_ok = await check_redis_health()
    chroma_ok = check_chroma_health()

    all_healthy = db_ok and chroma_ok
    status_code = "ok" if all_healthy else "degraded"

    logger.info(
        "Health check",
        status=status_code,
        db=db_ok,
        redis=redis_ok,
        chroma=chroma_ok,
    )

    return {
        "success": db_ok,
        "status": status_code,
        "services": {
            "database": "ok" if db_ok else "error",
            "redis": "ok" if redis_ok else "disabled",
            "chroma": "ok" if chroma_ok else "error",
        },
    }


@router.get("/version")
async def version() -> dict:
    """Returns application and API version information."""
    return {
        "success": True,
        "data": {
            "app_name": settings.app_name,
            "app_version": settings.app_version,
            "api_version": "v1",
            "environment": settings.environment,
        },
    }
