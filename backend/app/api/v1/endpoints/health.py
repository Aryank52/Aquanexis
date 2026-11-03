"""
Health and readiness endpoints for Kubernetes liveness/readiness probes.
"""

from datetime import datetime, timezone
from typing import Any, Dict

from fastapi import APIRouter
from sqlalchemy import text

from app.infrastructure.config import get_settings
from app.infrastructure.database import db_manager
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
    current_settings = get_settings()
    return {
        "status": "healthy",
        "mode": "demo" if current_settings.demo_mode else "database",
        "service": "aquanexis-backend",
        "version": "0.1.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/ready", summary="Readiness probe")
async def readiness_check() -> Dict[str, Any]:
    """
    Readiness probe - indicates if the application can serve traffic.
    Checks database connectivity (or DEMO_MODE engine) and critical dependencies.
    """
    current_settings = get_settings()
    checks = []
    overall_ready = True

    # Database connectivity or DEMO_MODE check
    if current_settings.demo_mode:
        checks.append(
            HealthCheck(
                "database",
                True,
                "DEMO_MODE active (simulator-backed in-memory repository; TimescaleDB bypassed)",
                {"mode": "DEMO_MODE", "simulated": True},
            ).to_dict()
        )
    else:
        try:
            async with db_manager.session() as db:
                await db.execute(text("SELECT 1"))
            checks.append(HealthCheck("database", True, "Database connection OK").to_dict())
        except Exception as e:
            logger.error("readiness_check_failed", check="database", error=str(e))
            checks.append(
                HealthCheck("database", False, f"Database connection failed: {e}").to_dict()
            )
            overall_ready = False

    # Configuration validation
    try:
        _ = current_settings.database.url
        _ = current_settings.auth.device_jwt_secret
        checks.append(HealthCheck("configuration", True, "Configuration valid").to_dict())
    except Exception as e:
        logger.error("readiness_check_failed", check="configuration", error=str(e))
        checks.append(HealthCheck("configuration", False, f"Configuration invalid: {e}").to_dict())
        overall_ready = False

    # Model artifacts (if ML enabled)
    if current_settings.ml.enabled:
        import os

        model_path = os.path.join(
            current_settings.ml.artifact_dir, current_settings.ml.rul_model_name
        )
        if os.path.exists(model_path):
            checks.append(
                HealthCheck(
                    "models", True, f"Model {current_settings.ml.rul_model_name} found"
                ).to_dict()
            )
        else:
            checks.append(
                HealthCheck(
                    "models",
                    False,
                    f"Model {current_settings.ml.rul_model_name} not found (using deterministic fallback — MODEL_MISSING)",
                ).to_dict()
            )
            if current_settings.is_production:
                overall_ready = False
    else:
        checks.append(HealthCheck("models", True, "ML disabled").to_dict())

    response = {
        "status": "ok" if overall_ready else "degraded",
        "ready": overall_ready,
        "mode": "demo" if current_settings.demo_mode else "database",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "checks": checks,
    }

    if not overall_ready:
        logger.warning("readiness_check_failed", checks=checks)

    return response


@router.get("/health/detailed", summary="Detailed health information")
async def detailed_health() -> Dict[str, Any]:
    """
    Detailed health information for debugging.
    Includes database stats, pool status, etc.
    """
    current_settings = get_settings()
    details: Dict[str, Any] = {
        "service": "aquanexis-backend",
        "version": "0.1.0",
        "environment": current_settings.env,
        "mode": "demo" if current_settings.demo_mode else "database",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    if current_settings.demo_mode:
        details["database"] = {
            "mode": "DEMO_MODE",
            "status": "simulator_backed_in_memory",
            "timescaledb_version": None,
            "disclosure": "Running in DEMO_MODE without TimescaleDB; all telemetry is SIMULATED.",
        }
    else:
        try:
            pool = db_manager.engine.pool
            details["database"] = {
                "pool_size": pool.size(),
                "checked_in": pool.checkedin(),
                "checked_out": pool.checkedout(),
                "overflow": pool.overflow(),
                "invalid": pool.invalid(),
            }
            async with db_manager.session() as db:
                result = await db.execute(text("SELECT version()"))
                details["database"]["version"] = result.scalar()

                result = await db.execute(
                    text("SELECT extversion FROM pg_extension WHERE extname = 'timescaledb'")
                )
                ts_version = result.scalar()
                details["database"]["timescaledb_version"] = ts_version
        except Exception as e:
            details["database"] = {"error": str(e)}

    details["settings"] = {
        "environment": current_settings.env,
        "demo_mode": current_settings.demo_mode,
        "ml_enabled": current_settings.ml.enabled,
        "safety_enabled": current_settings.safety.enabled,
        "allowed_origins": current_settings.allowed_origins,
    }

    return details
