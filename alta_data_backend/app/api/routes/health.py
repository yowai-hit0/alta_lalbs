from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from datetime import datetime, timezone
import redis
import os
from ...database import get_db
from ...config import settings

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/")
async def health_check():
    """Basic health check endpoint"""
    return {
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "service": "alta_data_backend",
        "version": "0.1.0"
    }


@router.get("/ready")
async def readiness_check(db: AsyncSession = Depends(get_db)):
    """Readiness check - verifies database connectivity"""
    try:
        # Test database connection
        await db.execute(text("SELECT 1"))
        
        # Test Redis connection
        redis_status = await test_redis_connection()
        
        return {
            "status": "ready",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "checks": {
                "database": "connected",
                "redis": redis_status
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail={
                "status": "not_ready",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "error": str(e),
                "checks": {
                    "database": "disconnected",
                    "redis": "unknown"
                }
            }
        )


@router.get("/live")
async def liveness_check():
    """Liveness check - verifies the service is running"""
    return {
        "status": "alive",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "uptime": "running"
    }


async def test_redis_connection() -> str:
    """Test Redis connection"""
    try:
        redis_client = redis.Redis.from_url(settings.redis_url)
        redis_client.ping()
        return "connected"
    except Exception:
        return "disconnected"


@router.get("/metrics")
async def metrics_endpoint():
    """Basic metrics endpoint"""
    # In production, you would collect actual metrics
    return {
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "metrics": {
            "requests_total": 0,  # Placeholder
            "requests_per_second": 0,  # Placeholder
            "error_rate": 0,  # Placeholder
            "response_time_ms": 0,  # Placeholder
        }
    }
