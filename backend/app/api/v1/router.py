"""
API v1 Router - Aggregates all v1 endpoints.
Includes DEMO_MODE / Auth router and fixes duplicate router prefixes on database-backed endpoints.
"""
from fastapi import APIRouter

from app.api.v1.endpoints import (
    alerts,
    dashboard,
    demo_api,
    diagnostics,
    filter_health,
    health,
    maintenance,
    notifications,
    purification_performance,
    safety,
    telemetry,
    water_quality,
)
from app.infrastructure.config import get_settings

settings = get_settings()
api_router = APIRouter()

# Health endpoints (no prefix)
api_router.include_router(health.router)

# Auth, Demo Control, and DEMO_MODE simulator-backed endpoints
api_router.include_router(demo_api.router)

# Database-backed endpoints (prefixes are already defined on each sub-router)
if not settings.demo_mode:
    api_router.include_router(telemetry.router, tags=["telemetry"])
    api_router.include_router(alerts.router, tags=["alerts"])
    api_router.include_router(water_quality.router, tags=["water-quality"])
    api_router.include_router(filter_health.router, tags=["filter-health"])
    api_router.include_router(purification_performance.router, tags=["purification-performance"])
    api_router.include_router(diagnostics.router, tags=["diagnostics"])
    api_router.include_router(safety.router, tags=["safety"])
    api_router.include_router(notifications.router, tags=["notifications"])
    api_router.include_router(maintenance.router, tags=["maintenance"])
    api_router.include_router(dashboard.router, tags=["dashboard"])
