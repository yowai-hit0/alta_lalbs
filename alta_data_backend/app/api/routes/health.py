from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from datetime import datetime, timezone
import redis
import os
from typing import Dict, Any
from ...database import get_db
from ...config import settings
from ...core.storage import is_gcs_available
from ...core.document_ai import document_ai_service
from ...core.speech_to_text import speech_to_text_service
from ...core.email import is_email_available

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


@router.get("/services")
async def services_health_check():
    """Check the availability of all external services"""
    services_status = {
        "google_cloud_storage": {
            "available": is_gcs_available(),
            "status": "available" if is_gcs_available() else "not_configured"
        },
        "document_ai": {
            "available": document_ai_service.is_available(),
            "status": "available" if document_ai_service.is_available() else "not_configured"
        },
        "speech_to_text": {
            "available": speech_to_text_service.is_available(),
            "status": "available" if speech_to_text_service.is_available() else "not_configured"
        },
        "email": {
            "available": is_email_available(),
            "status": "available" if is_email_available() else "not_configured"
        }
    }
    
    # Determine overall status
    all_available = all(service["available"] for service in services_status.values())
    overall_status = "all_services_available" if all_available else "some_services_unavailable"
    
    return {
        "status": overall_status,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "services": services_status,
        "message": "All services are available" if all_available else "Some services are not configured but the application will continue to run"
    }


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
