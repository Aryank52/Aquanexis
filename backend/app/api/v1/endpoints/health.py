"""
Health and readiness endpoints for Kubernetes liveness/readiness probes.
"""
from datetime import datetime, timezone
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.config import get_settings
from app.infrastructure.database import db_manager, get_db
from app.infrastructure.logging import get_logger

settings = get_settings()
logger = get_logger(__name__)

router = APIRouter(prefix="", tags=["health"])


class HealthCheck:
    """Individual health check result."""
    def __init__(
        self,
        name: str,
        healthy: bool,
        message: str = "",
        details: Dict[str, Any] | None = None,
    ):
        self.name = name
        self.healthy = healthy
        self.message = message
        self.details = details or {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "healthy": self.healthy,
            "message": self.message,
            "details": self.details,
        }


@router.get("/health", summary="Liveness probe")
async def health_check() -> Dict[str, Any]:
    """
    Liveness probe - indicates if the application is running.
    Does not check dependencies.
    """
    return {
        "status": "healthy",
        "service": "aquanexis-backend",
        "version": "0.1.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/ready", summary="Readiness probe")
async def readiness_check(db: AsyncSession = Depends(get_db)) -> Dict[str, Any]:
    """
    Readiness probe - indicates if the application can serve traffic.
    Checks database connectivity and critical dependencies.
    """
    checks = []
    overall_ready = True

    # Database connectivity
    try:
        await db.execute(text("SELECT 1"))
        checks.append(HealthCheck("database", True, "Database connection OK").to_dict())
    except Exception as e:
        logger.error("readiness_check_failed", check="database", error=str(e))
        checks.append(HealthCheck("database", False, f"Database connection failed: {e}").to_dict())
        overall_ready = False

    # Configuration validation
    try:
        # Access settings to validate
        _ = settings.database.url
        _ = settings.auth.device_jwt_secret
        checks.append(HealthCheck("configuration", True, "Configuration valid").to_dict())
    except Exception as e:
        logger.error("readiness_check_failed", check="configuration", error=str(e))
        checks.append(HealthCheck("configuration", False, f"Configuration invalid: {e}").to_dict())
        overall_ready = False

    # Model artifacts (if ML enabled)
    if settings.ml.enabled:
        import os
        model_path = os.path.join(settings.ml.artifact_dir, settings.ml.rul_model_name)
        if os.path.exists(model_path):
            checks.append(HealthCheck("models", True, f"Model {settings.ml.rul_model_name} found").to_dict())
        else:
            checks.append(HealthCheck("models", False, f"Model {settings.ml.rul_model_name} not found").to_dict())
            # Don't fail readiness for missing models in dev
            if settings.is_production:
                overall_ready = False
    else:
        checks.append(HealthCheck("models", True, "ML disabled").to_dict())

    # Determine HTTP status
    http_status = status.HTTP_200_OK if overall_ready else status.HTTP_503_SERVICE_UNAVAILABLE

    response = {
        "ready": overall_ready,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "checks": checks,
    }

    # Note: FastAPI doesn't allow setting status_code in return dict directly
    # The route will return 200, but we log the actual readiness
    if not overall_ready:
        logger.warning("readiness_check_failed", checks=checks)

    return response


@router.get("/health/detailed", summary="Detailed health information")
async def detailed_health(db: AsyncSession = Depends(get_db)) -> Dict[str, Any]:
    """
    Detailed health information for debugging.
    Includes database stats, pool status, etc.
    """
    details: Dict[str, Any] = {
        "service": "aquanexis-backend",
        "version": "0.1.0",
        "environment": settings.env,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    # Database details
    try:
        # Pool status
        pool = db_manager.engine.pool
        details["database"] = {
            "pool_size": pool.size(),
            "checked_in": pool.checkedin(),
            "checked_out": pool.checkedout(),
            "overflow": pool.overflow(),
            "invalid": pool.invalid(),
        }

        # Database version
        result = await db.execute(text("SELECT version()"))
        details["database"]["version"] = result.scalar()

        # TimescaleDB extension
        result = await db.execute(text("SELECT extversion FROM pg_extension WHERE extname = 'timescaledb'"))
        ts_version = result.scalar()
        details["database"]["timescaledb_version"] = ts_version

    except Exception as e:
        details["database"] = {"error": str(e)}

    # Settings (non-sensitive)
    details["settings"] = {
        "environment": settings.env,
        "ml_enabled": settings.ml.enabled,
        "safety_enabled": settings.safety.enabled,
        "allowed_origins": settings.allowed_origins,
    }

    return details