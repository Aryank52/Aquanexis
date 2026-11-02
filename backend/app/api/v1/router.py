"""
API v1 Router - Aggregates all v1 endpoints.
"""
from fastapi import APIRouter

from app.api.v1.endpoints import health, telemetry, alerts, water_quality, filter_health, purification_performance, diagnostics, safety, notifications, maintenance, dashboard

api_router = APIRouter()

# Health endpoints (no prefix)
api_router.include_router(health.router)

# Telemetry endpoints
api_router.include_router(telemetry.router, prefix="/telemetry", tags=["telemetry"])

# Alert endpoints
api_router.include_router(alerts.router, prefix="/alerts", tags=["alerts"])

# Water Quality endpoints
api_router.include_router(water_quality.router, prefix="/water-quality", tags=["water-quality"])

# Filter Health endpoints
api_router.include_router(filter_health.router, prefix="/filter-health", tags=["filter-health"])

# Purification Performance endpoints
api_router.include_router(purification_performance.router, prefix="/purification-performance", tags=["purification-performance"])

# Diagnostics endpoints
api_router.include_router(diagnostics.router, prefix="/diagnostics", tags=["diagnostics"])

# Safety endpoints
api_router.include_router(safety.router, prefix="/safety", tags=["safety"])

# Notification endpoints
api_router.include_router(notifications.router, prefix="/notifications", tags=["notifications"])

# Maintenance endpoints
api_router.include_router(maintenance.router, prefix="/maintenance", tags=["maintenance"])

# Dashboard endpoints
api_router.include_router(dashboard.router, prefix="/devices", tags=["dashboard"])

# api_router.include_router(devices.router, prefix="/devices", tags=["devices"])