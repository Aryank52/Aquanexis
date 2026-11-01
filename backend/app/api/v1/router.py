"""
API v1 Router - Aggregates all v1 endpoints.
"""
from fastapi import APIRouter

from app.api.v1.endpoints import health, telemetry, alerts

api_router = APIRouter()

# Health endpoints (no prefix)
api_router.include_router(health.router)

# Telemetry endpoints
api_router.include_router(telemetry.router, prefix="/telemetry", tags=["telemetry"])

# Alert endpoints
api_router.include_router(alerts.router, prefix="/alerts", tags=["alerts"])

# api_router.include_router(devices.router, prefix="/devices", tags=["devices"])
# api_router.include_router(water_quality.router, prefix="/water-quality", tags=["water-quality"])
# api_router.include_router(filter_health.router, prefix="/filter-health", tags=["filter-health"])
# api_router.include_router(diagnostics.router, prefix="/diagnostics", tags=["diagnostics"])
# api_router.include_router(maintenance.router, prefix="/maintenance", tags=["maintenance"])