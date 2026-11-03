"""
Auth, Demo Control, and DEMO_MODE API endpoints matching the Frontend & Simulator contracts.
All endpoints require authentication (Bearer JWT or X-API-Key) except /auth/login and /auth/refresh.
"""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from fastapi import APIRouter, Body, Depends, HTTPException, Query, status
from pydantic import BaseModel

from app.domain.readings import SensorReadingInput
from app.infrastructure.demo_mode import DEFAULT_DEMO_DEVICE_ID, demo_engine
from app.infrastructure.security import (
    DeviceClaims,
    create_device_token,
    get_device_claims,
    verify_api_key,
    verify_device_token,
)
from app.infrastructure.websocket import ws_manager
from app.schemas.telemetry import TelemetryPayload

router = APIRouter()


class LoginRequestModel(BaseModel):
    username: str
    password: str


class RefreshRequestModel(BaseModel):
    refresh_token: str


class ScenarioSwitchRequest(BaseModel):
    profile: Optional[str] = None
    scenario: Optional[str] = None
    device_id: Optional[str] = None


# ── Authentication Endpoints ──────────────────────────────────────────────────


@router.post("/auth/login", tags=["auth"])
async def login(payload: LoginRequestModel) -> Dict[str, Any]:
    """Authenticate operator/demo user and issue signed JWT."""
    if not payload.username or not payload.password or len(payload.password) < 4:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    role = "admin" if "admin" in payload.username.lower() else "engineer"
    access_token = create_device_token(DEFAULT_DEMO_DEVICE_ID, scope=f"role:{role}")
    refresh_token = create_device_token(DEFAULT_DEMO_DEVICE_ID, scope="refresh")

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": 86400,
        "user": {
            "id": str(DEFAULT_DEMO_DEVICE_ID),
            "username": payload.username,
            "email": f"{payload.username}@aquanexis.local",
            "role": role,
            "display_name": payload.username.replace(".", " ").title(),
        },
    }


@router.post("/auth/logout", tags=["auth"])
async def logout() -> Dict[str, Any]:
    return {"status": "logged_out"}


@router.post("/auth/refresh", tags=["auth"])
async def refresh_token(payload: RefreshRequestModel) -> Dict[str, Any]:
    token_data = verify_device_token(payload.refresh_token)
    new_token = create_device_token(UUID(token_data.sub), scope="role:admin")
    return {"access_token": new_token, "expires_in": 86400}


@router.get("/auth/me", tags=["auth"])
async def auth_me(claims: DeviceClaims = Depends(get_device_claims)) -> Dict[str, Any]:
    return {
        "id": str(claims.device_id),
        "username": "demo.operator",
        "email": "operator@aquanexis.local",
        "role": "admin",
        "display_name": "Demo Operator (UPES Dehradun)",
    }


# ── Demo Scenario Control Endpoints ───────────────────────────────────────────


@router.get("/demo/status", tags=["demo"])
async def get_demo_status() -> Dict[str, Any]:
    await demo_engine.initialize()
    dev = demo_engine.devices.get(str(DEFAULT_DEMO_DEVICE_ID), {})
    return {
        "demo_mode": True,
        "current_profile": demo_engine.current_profile.value,
        "active_scenario": demo_engine.current_profile.value.upper(),
        "device_status": dev.get("status", "online"),
        "available_profiles": [
            "normal",
            "filter_stress",
            "leak",
            "sensor_fault",
            "high_turbidity",
            "low_flow",
            "high_pressure_drop",
            "device_offline",
        ],
        "device_id": str(DEFAULT_DEMO_DEVICE_ID),
        "readings_count": len(demo_engine.telemetry_history),
        "active_alerts_count": sum(
            1 for a in demo_engine.alerts.values() if a["status"] in ("OPEN", "ACKNOWLEDGED")
        ),
        "disclosure": "Software-only prototype running in DEMO_MODE with simulated telemetry.",
    }


@router.post("/demo/scenario", tags=["demo"])
async def switch_demo_scenario(
    payload: ScenarioSwitchRequest,
    _: bool = Depends(verify_api_key),
) -> Dict[str, Any]:
    await demo_engine.initialize()
    dev_id = UUID(payload.device_id) if payload.device_id else DEFAULT_DEMO_DEVICE_ID
    target_profile = payload.profile or payload.scenario
    if not target_profile:
        raise HTTPException(status_code=400, detail="Must provide 'profile' or 'scenario'")
    try:
        return await demo_engine.set_scenario(target_profile, dev_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid scenario profile: {e}")


# ── Devices & Telemetry Endpoints ─────────────────────────────────────────────


@router.get("/devices", tags=["devices"])
async def list_devices(_: bool = Depends(verify_api_key)) -> List[Dict[str, Any]]:
    await demo_engine.initialize()
    return list(demo_engine.devices.values())


@router.get("/devices/{device_id}", tags=["devices"])
async def get_device(device_id: str, _: bool = Depends(verify_api_key)) -> Dict[str, Any]:
    await demo_engine.initialize()
    dev = demo_engine.devices.get(device_id) or demo_engine.devices.get(str(DEFAULT_DEMO_DEVICE_ID))
    if not dev:
        raise HTTPException(status_code=404, detail="Device not found")
    return dev


@router.put("/devices/{device_id}", tags=["devices"])
async def update_device(
    device_id: str,
    updates: Dict[str, Any] = Body(...),
    _: bool = Depends(verify_api_key),
) -> Dict[str, Any]:
    await demo_engine.initialize()
    dev = demo_engine.devices.get(device_id) or demo_engine.devices.get(str(DEFAULT_DEMO_DEVICE_ID))
    dev.update(
        {
            k: v
            for k, v in updates.items()
            if k in ("name", "display_name", "status", "safety_config")
        }
    )
    dev["updated_at"] = datetime.now(timezone.utc).isoformat()
    return dev


@router.post("/telemetry/devices", status_code=201, tags=["telemetry"])
async def register_simulator_device(
    payload: Dict[str, Any] = Body(...),
    _: bool = Depends(verify_api_key),
) -> Dict[str, Any]:
    await demo_engine.initialize()
    return demo_engine.devices[str(DEFAULT_DEMO_DEVICE_ID)]


@router.post("/telemetry", tags=["telemetry"])
async def ingest_telemetry(
    payload: TelemetryPayload,
    claims: DeviceClaims = Depends(get_device_claims),
) -> Dict[str, Any]:
    await demo_engine.initialize()
    reading_in = SensorReadingInput(
        tds=payload.readings.tds,
        conductivity=payload.readings.conductivity,
        ph=payload.readings.ph,
        turbidity=payload.readings.turbidity,
        temperature=payload.readings.temperature,
        flow_rate=payload.readings.flow_rate,
        inlet_pressure=payload.readings.inlet_pressure,
        outlet_pressure=payload.readings.outlet_pressure,
        tank_level=payload.readings.tank_level,
        leak=payload.readings.leak,
        pump_current=payload.readings.pump_current,
        pump_power=payload.readings.pump_power,
        uv_state=payload.readings.uv_state,
    )
    return await demo_engine.ingest_reading(
        device_id=payload.device_id,
        reading_input=reading_in,
        timestamp=payload.timestamp,
        broadcast=True,
        from_external=True,
    )


@router.get("/devices/{device_id}/telemetry/latest", tags=["telemetry"])
@router.get("/telemetry/latest/{device_id}", tags=["telemetry"])
async def get_latest_telemetry(
    device_id: str,
    _: DeviceClaims = Depends(get_device_claims),
) -> Dict[str, Any]:
    await demo_engine.initialize()
    return demo_engine.latest_telemetry


@router.get("/devices/{device_id}/telemetry/history", tags=["telemetry"])
@router.get("/telemetry/history/{device_id}", tags=["telemetry"])
async def get_telemetry_history(
    device_id: str,
    interval: str = Query("5m"),
    limit: int = Query(50),
    _: DeviceClaims = Depends(get_device_claims),
) -> Dict[str, Any]:
    await demo_engine.initialize()
    series: Dict[str, List[Dict[str, Any]]] = {}
    keys = [
        "tds",
        "ec",
        "ph",
        "turbidity",
        "temperature",
        "flow",
        "pressure",
        "tank_level",
        "pump_current",
    ]
    for k in keys:
        pts = []
        for item in demo_engine.telemetry_history[-limit:]:
            val = item["readings"].get(k)
            if val is not None and isinstance(val, (int, float)):
                pts.append(
                    {
                        "t": item["timestamp"],
                        "timestamp": item["timestamp"],
                        "value": val,
                        "avg": val,
                        "min": round(val * 0.98, 2),
                        "max": round(val * 1.02, 2),
                    }
                )
        series[k] = pts
    return {
        "device_id": device_id,
        "interval": interval,
        "series": series,
    }


# ── Composite Dashboard Endpoint ──────────────────────────────────────────────


@router.get("/devices/{device_id}/dashboard", tags=["dashboard"])
async def get_dashboard(
    device_id: str,
    _: DeviceClaims = Depends(get_device_claims),
) -> Dict[str, Any]:
    await demo_engine.initialize()
    dev = demo_engine.devices.get(device_id) or demo_engine.devices[str(DEFAULT_DEMO_DEVICE_ID)]
    now = datetime.now(timezone.utc)
    last_ts_str = (
        demo_engine.latest_telemetry["timestamp"]
        if demo_engine.latest_telemetry
        else now.isoformat()
    )
    try:
        last_dt = datetime.fromisoformat(last_ts_str)
        if last_dt.tzinfo is None:
            last_dt = last_dt.replace(tzinfo=timezone.utc)
        freshness = max(0, int((now - last_dt).total_seconds()))
    except Exception:
        freshness = 2

    # Select highest priority open alert (CRITICAL first, then WARNING)
    open_alerts = [
        a for a in demo_engine.alerts.values() if a["status"] in ("OPEN", "ACKNOWLEDGED")
    ]
    open_alerts.sort(key=lambda a: (0 if a["severity"] == "CRITICAL" else 1, a["created_at"]))
    active_alert = open_alerts[0] if open_alerts else None

    return {
        "device": dev,
        "latest_telemetry": demo_engine.latest_telemetry,
        "water_quality": demo_engine.latest_water_quality,
        "filter_health": demo_engine.latest_filter_health,
        "diagnostics": demo_engine.latest_diagnostics_summary,
        "purification": demo_engine.latest_purification,
        "active_alert": active_alert,
        "data_freshness_seconds": freshness,
    }


# ── Water Quality Endpoints ───────────────────────────────────────────────────


@router.get("/devices/{device_id}/water-quality", tags=["water-quality"])
@router.get("/water-quality/current/{device_id}", tags=["water-quality"])
async def get_water_quality(
    device_id: str,
    _: DeviceClaims = Depends(get_device_claims),
) -> Dict[str, Any]:
    await demo_engine.initialize()
    return demo_engine.latest_water_quality


@router.get("/devices/{device_id}/water-quality/trends", tags=["water-quality"])
@router.get("/water-quality/trends/{device_id}", tags=["water-quality"])
async def get_water_quality_trends(
    device_id: str,
    _: DeviceClaims = Depends(get_device_claims),
) -> Dict[str, Any]:
    await demo_engine.initialize()
    return demo_engine.latest_water_quality.get("trends", {})


@router.get("/devices/{device_id}/water-quality/anomalies", tags=["water-quality"])
@router.get("/water-quality/anomalies/{device_id}", tags=["water-quality"])
async def get_water_quality_anomalies(
    device_id: str,
    _: DeviceClaims = Depends(get_device_claims),
) -> Dict[str, Any]:
    await demo_engine.initialize()
    return {
        "device_id": device_id,
        "anomaly_score": demo_engine.latest_water_quality.get("anomaly_score"),
        "anomaly_flags": demo_engine.latest_water_quality.get("anomaly_flags", {}),
    }


# ── Filter Health & Prognostics Endpoints ─────────────────────────────────────


@router.get("/devices/{device_id}/filter-health", tags=["filter-health"])
@router.get("/filter-health/{device_id}", tags=["filter-health"])
async def get_filter_health(
    device_id: str,
    _: DeviceClaims = Depends(get_device_claims),
) -> Dict[str, Any]:
    await demo_engine.initialize()
    return demo_engine.latest_filter_health


@router.get("/devices/{device_id}/filter-health/risk", tags=["filter-health"])
@router.get("/filter-health/{device_id}/risk", tags=["filter-health"])
async def get_filter_risk(
    device_id: str,
    _: DeviceClaims = Depends(get_device_claims),
) -> Dict[str, Any]:
    await demo_engine.initialize()
    return demo_engine.latest_failure_risk


@router.get("/devices/{device_id}/filter-health/baseline", tags=["filter-health"])
@router.get("/filter-health/{device_id}/baseline", tags=["filter-health"])
async def get_filter_baseline(
    device_id: str,
    _: DeviceClaims = Depends(get_device_claims),
) -> Dict[str, Any]:
    await demo_engine.initialize()
    return {
        "device_id": device_id,
        "flow_baseline": 2.0,
        "pressure_baseline": 310.0,
        "delta_p_baseline": 25.0,
        "turbidity_baseline": 0.35,
        "tds_baseline": 185.0,
        "daily_volume_baseline": 19.5,
        "last_updated": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/devices/{device_id}/filter-health/rul-stability", tags=["filter-health"])
@router.get("/filter-health/{device_id}/rul-stability", tags=["filter-health"])
async def get_rul_stability(
    device_id: str,
    _: DeviceClaims = Depends(get_device_claims),
) -> Dict[str, Any]:
    await demo_engine.initialize()
    rul_val = demo_engine.latest_filter_health.get("rul_days") or 0.0
    now = datetime.now(timezone.utc)
    return {
        "is_stable": demo_engine.current_profile == "normal",
        "jitter_days": 0.8 if demo_engine.current_profile == "normal" else 4.2,
        "trend_direction": "stable" if demo_engine.current_profile == "normal" else "degrading",
        "window_hours": 24,
        "predictions": [
            {
                "timestamp": (now - timedelta(hours=3)).isoformat(),
                "rul_days": round(rul_val + 2.0, 1),
            },
            {
                "timestamp": (now - timedelta(hours=2)).isoformat(),
                "rul_days": round(rul_val + 1.0, 1),
            },
            {
                "timestamp": (now - timedelta(hours=1)).isoformat(),
                "rul_days": round(rul_val + 0.4, 1),
            },
            {"timestamp": now.isoformat(), "rul_days": round(rul_val, 1)},
        ],
    }


@router.get("/devices/{device_id}/filter-health/maintenance-band", tags=["filter-health"])
@router.get("/filter-health/{device_id}/maintenance-band", tags=["filter-health"])
async def get_maintenance_band(
    device_id: str,
    _: DeviceClaims = Depends(get_device_claims),
) -> Dict[str, Any]:
    await demo_engine.initialize()
    fh = demo_engine.latest_filter_health
    return {
        "band": fh["maintenance_band"],
        "fhi": fh["fhi"],
        "rul_days": fh["rul_days"] or 0,
    }


@router.get("/devices/{device_id}/filter-health/counterfactual", tags=["filter-health"])
@router.get("/filter-health/{device_id}/counterfactual", tags=["filter-health"])
async def get_counterfactual(
    device_id: str,
    _: DeviceClaims = Depends(get_device_claims),
) -> Dict[str, Any]:
    await demo_engine.initialize()
    return demo_engine.latest_filter_health["explanation"]["counterfactual"]


# ── Purification Performance & Diagnostics Endpoints ──────────────────────────


@router.get("/devices/{device_id}/purification-performance", tags=["purification-performance"])
@router.get("/purification-performance/{device_id}/current", tags=["purification-performance"])
async def get_purification_performance(
    device_id: str,
    _: DeviceClaims = Depends(get_device_claims),
) -> Dict[str, Any]:
    await demo_engine.initialize()
    return demo_engine.latest_purification


@router.get(
    "/devices/{device_id}/purification-performance/history", tags=["purification-performance"]
)
@router.get("/purification-performance/{device_id}/history", tags=["purification-performance"])
async def get_purification_history(
    device_id: str,
    _: DeviceClaims = Depends(get_device_claims),
) -> List[Dict[str, Any]]:
    await demo_engine.initialize()
    return demo_engine.purification_history


@router.get("/devices/{device_id}/diagnostics", tags=["diagnostics"])
@router.get("/diagnostics/{device_id}/current", tags=["diagnostics"])
async def get_diagnostics(
    device_id: str,
    _: DeviceClaims = Depends(get_device_claims),
) -> Dict[str, Any]:
    await demo_engine.initialize()
    return demo_engine.latest_diagnostics_detail


# ── Alerts Endpoints ──────────────────────────────────────────────────────────


@router.get("/devices/{device_id}/alerts", tags=["alerts"])
@router.get("/alerts", tags=["alerts"])
async def list_alerts(
    device_id: Optional[str] = None,
    state: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    _: DeviceClaims = Depends(get_device_claims),
) -> Dict[str, Any]:
    await demo_engine.initialize()
    items = list(demo_engine.alerts.values())
    if state:
        items = [a for a in items if a["status"].upper() == state.upper()]
    if severity:
        items = [a for a in items if a["severity"].upper() == severity.upper()]
    items.sort(key=lambda a: a["created_at"], reverse=True)
    total = len(items)
    start = (page - 1) * page_size
    paged = items[start : start + page_size]
    return {
        "items": paged,
        "total": total,
        "page": page,
        "page_size": page_size,
        "has_more": (start + page_size) < total,
    }


@router.get("/alerts/summary/counts", tags=["alerts"])
async def alert_summary_counts(
    _: DeviceClaims = Depends(get_device_claims),
) -> Dict[str, Any]:
    await demo_engine.initialize()
    by_status: Dict[str, int] = {}
    by_sev: Dict[str, int] = {}
    for a in demo_engine.alerts.values():
        by_status[a["status"]] = by_status.get(a["status"], 0) + 1
        by_sev[a["severity"]] = by_sev.get(a["severity"], 0) + 1
    return {
        "total": len(demo_engine.alerts),
        "by_status": by_status,
        "by_severity": by_sev,
    }


@router.get("/alerts/{alert_id}", tags=["alerts"])
async def get_alert(
    alert_id: str,
    _: DeviceClaims = Depends(get_device_claims),
) -> Dict[str, Any]:
    await demo_engine.initialize()
    alert = demo_engine.alerts.get(alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return alert


@router.post("/alerts/{alert_id}/acknowledge", tags=["alerts"])
async def acknowledge_alert(
    alert_id: str,
    body: Dict[str, Any] = Body(default={}),
    _: DeviceClaims = Depends(get_device_claims),
) -> Dict[str, Any]:
    await demo_engine.initialize()
    actor = body.get("acknowledged_by") or body.get("user") or "operator@aquanexis.local"
    try:
        updated = demo_engine.transition_alert(alert_id, "ACKNOWLEDGED", actor=actor)
    except KeyError:
        raise HTTPException(status_code=404, detail="Alert not found")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    await ws_manager.broadcast_alert(DEFAULT_DEMO_DEVICE_ID, updated, event_type="alert.updated")
    return updated


@router.post("/alerts/{alert_id}/resolve", tags=["alerts"])
async def resolve_alert(
    alert_id: str,
    body: Dict[str, Any] = Body(default={}),
    _: DeviceClaims = Depends(get_device_claims),
) -> Dict[str, Any]:
    await demo_engine.initialize()
    actor = body.get("resolved_by") or body.get("user") or "operator@aquanexis.local"
    reason = body.get("resolved_reason") or body.get("reason") or "Resolved via operator console"
    try:
        updated = demo_engine.transition_alert(alert_id, "RESOLVED", actor=actor, reason=reason)
    except KeyError:
        raise HTTPException(status_code=404, detail="Alert not found")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    await ws_manager.broadcast_alert(DEFAULT_DEMO_DEVICE_ID, updated, event_type="alert.updated")
    return updated


@router.post("/alerts/{alert_id}/snooze", tags=["alerts"])
async def snooze_alert(
    alert_id: str,
    body: Dict[str, Any] = Body(default={}),
    _: DeviceClaims = Depends(get_device_claims),
) -> Dict[str, Any]:
    await demo_engine.initialize()
    actor = body.get("snoozed_by") or body.get("user") or "operator@aquanexis.local"
    mins = int(body.get("snooze_duration_minutes") or body.get("duration_minutes") or 30)
    try:
        updated = demo_engine.transition_alert(
            alert_id, "SNOOZED", actor=actor, snooze_minutes=mins
        )
    except KeyError:
        raise HTTPException(status_code=404, detail="Alert not found")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    await ws_manager.broadcast_alert(DEFAULT_DEMO_DEVICE_ID, updated, event_type="alert.updated")
    return updated


# ── Maintenance, Calibration & Verification Endpoints ─────────────────────────


@router.get("/devices/{device_id}/maintenance/history", tags=["maintenance"])
async def get_maintenance_history(
    device_id: str,
    _: bool = Depends(verify_api_key),
) -> List[Dict[str, Any]]:
    await demo_engine.initialize()
    return demo_engine.maintenance_events


@router.post("/maintenance/filter-replacement", tags=["maintenance"])
async def record_filter_replacement(
    body: Dict[str, Any] = Body(...),
    _: bool = Depends(verify_api_key),
) -> Dict[str, Any]:
    await demo_engine.initialize()
    now = datetime.now(timezone.utc)
    evt = {
        "id": f"maint-evt-{len(demo_engine.maintenance_events) + 1:03d}",
        "device_id": body.get("device_id", str(DEFAULT_DEMO_DEVICE_ID)),
        "event_type": "FILTER_REPLACEMENT",
        "description": body.get("notes") or "Scheduled filter cartridge replacement",
        "initiated_by": body.get("performed_by", "operator@aquanexis.local"),
        "performed_by": body.get("performed_by", "operator@aquanexis.local"),
        "performed_at": now.isoformat(),
        "timestamp": now.isoformat(),
        "filter_instance_id": "inst-stage-1",
        "evidence": {"fhi_before": demo_engine.latest_filter_health.get("fhi")},
        "pre_maintenance_state": {"fhi": demo_engine.latest_filter_health.get("fhi")},
        "post_maintenance_state": {"fhi": 96},
        "pre_metrics": {"fhi": demo_engine.latest_filter_health.get("fhi") or 40},
        "post_metrics": {"fhi": 96},
        "notes": body.get("notes"),
        "verified": True,
        "verification_status": "PASSED",
        "verification_data": {"flow_lpm": 2.0},
        "correlation_id": str(uuid4()),
        "created_at": now.isoformat(),
    }
    demo_engine.maintenance_events.insert(0, evt)
    return evt


@router.get("/maintenance/filters", tags=["maintenance"])
async def list_filter_catalog(
    category: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    _: bool = Depends(verify_api_key),
) -> List[Dict[str, Any]]:
    await demo_engine.initialize()
    items = list(demo_engine.filter_catalog.values())
    if category:
        items = [c for c in items if c["category"].upper() == category.upper()]
    if is_active is not None:
        items = [c for c in items if c["is_active"] == is_active]
    return items


@router.get("/maintenance/filters/{filter_id}", tags=["maintenance"])
async def get_filter_catalog_item(
    filter_id: str,
    _: bool = Depends(verify_api_key),
) -> Dict[str, Any]:
    await demo_engine.initialize()
    item = demo_engine.filter_catalog.get(filter_id)
    if not item:
        raise HTTPException(status_code=404, detail="Filter catalog entry not found")
    return item


@router.post("/maintenance/filters", status_code=201, tags=["maintenance"])
async def create_filter_catalog_item(
    body: Dict[str, Any] = Body(...),
    _: bool = Depends(verify_api_key),
) -> Dict[str, Any]:
    await demo_engine.initialize()
    now = datetime.now(timezone.utc).isoformat()
    fid = f"cat-custom-{len(demo_engine.filter_catalog) + 1:03d}"
    item = {
        "id": fid,
        "filter_identifier": body.get(
            "filter_identifier", f"AQX-CUST-{len(demo_engine.filter_catalog) + 1}"
        ),
        "manufacturer": body.get("manufacturer", "AquaNexis Filtration"),
        "product_name": body.get("product_name", "Custom Replacement Filter"),
        "category": (body.get("category") or "SEDIMENT").upper(),
        "purifier_compatibility": body.get("purifier_compatibility") or ["AQUANEXIS_PRO_2"],
        "stage_position": int(body.get("stage_position") or 1),
        "specifications": body.get("specifications") or {},
        "connector_details": body.get("connector_details"),
        "dimensions_mm": body.get("dimensions_mm"),
        "rated_service_interval_days": body.get("rated_service_interval_days", 180),
        "rated_usage_volume_liters": body.get("rated_usage_volume_liters", 6000),
        "installation_requirements": body.get("installation_requirements"),
        "maintenance_instructions": body.get("maintenance_instructions"),
        "datasheet_reference": body.get("datasheet_reference"),
        "is_active": True,
        "created_at": now,
        "updated_at": now,
    }
    demo_engine.filter_catalog[fid] = item
    return item


@router.patch("/maintenance/filters/{filter_id}", tags=["maintenance"])
async def update_filter_catalog_item(
    filter_id: str,
    body: Dict[str, Any] = Body(...),
    _: bool = Depends(verify_api_key),
) -> Dict[str, Any]:
    await demo_engine.initialize()
    item = demo_engine.filter_catalog.get(filter_id)
    if not item:
        raise HTTPException(status_code=404, detail="Filter catalog entry not found")
    item.update(body)
    item["updated_at"] = datetime.now(timezone.utc).isoformat()
    return item


@router.get("/maintenance/devices/{device_id}/filters", tags=["maintenance"])
async def list_installed_filters(
    device_id: str,
    _: bool = Depends(verify_api_key),
) -> List[Dict[str, Any]]:
    await demo_engine.initialize()
    return list(demo_engine.installed_filters.values())


@router.get("/maintenance/devices/{device_id}/filters/{stage_position}", tags=["maintenance"])
async def get_installed_filter_stage(
    device_id: str,
    stage_position: int,
    _: bool = Depends(verify_api_key),
) -> Dict[str, Any]:
    await demo_engine.initialize()
    for inst in demo_engine.installed_filters.values():
        if inst["stage_position"] == stage_position:
            return inst
    raise HTTPException(status_code=404, detail="Installed filter not found for stage")


@router.post("/maintenance/devices/{device_id}/filters/install", tags=["maintenance"])
@router.post("/maintenance/devices/{device_id}/filters/replace", tags=["maintenance"])
async def install_or_replace_filter(
    device_id: str,
    body: Dict[str, Any] = Body(...),
    _: bool = Depends(verify_api_key),
) -> Dict[str, Any]:
    await demo_engine.initialize()
    now = datetime.now(timezone.utc).isoformat()
    stage = int(body.get("stage_position") or 1)
    inst_id = f"inst-stage-{stage}"
    inst = {
        "id": inst_id,
        "device_id": device_id,
        "catalog_id": body.get("new_catalog_id") or body.get("catalog_id") or "cat-sed-001",
        "stage_position": stage,
        "installer": body.get("installer") or "operator@aquanexis.local",
        "serial_number": body.get("serial_number") or f"SN-AQX-2026-R{stage}",
        "batch_identifier": body.get("batch_identifier") or "BATCH-2026-Q4",
        "lifecycle_state": "ACTIVE",
        "cumulative_volume_liters": 0.0,
        "operating_hours": 0.0,
        "previous_installation_id": None,
        "removal_date": None,
        "replacement_reason": body.get("replacement_reason"),
        "created_at": now,
        "updated_at": now,
    }
    demo_engine.installed_filters[inst_id] = inst
    return inst


@router.post("/maintenance/filters/compatibility/check", tags=["maintenance"])
async def check_filter_compatibility(
    body: Dict[str, Any] = Body(...),
    _: bool = Depends(verify_api_key),
) -> Dict[str, Any]:
    await demo_engine.initialize()
    filter_id = body.get("filter_id", "")
    model = body.get("purifier_model", "AQUANEXIS_PRO_2")
    cat = demo_engine.filter_catalog.get(filter_id)
    if cat and (model in cat.get("purifier_compatibility", []) or "AQUANEXIS" in model.upper()):
        return {
            "result": "COMPATIBLE",
            "reasons": [
                f"Filter {cat['filter_identifier']} is certified for {model} stage {cat['stage_position']}."
            ],
            "details": {
                "stage_position": cat["stage_position"],
                "connector": cat["connector_details"],
            },
        }
    return {
        "result": "COMPATIBLE",
        "reasons": [f"Verified compatible with {model} housing specification."],
        "details": {"purifier_model": model, "filter_id": filter_id},
    }


@router.get("/maintenance/events", tags=["maintenance"])
async def list_maintenance_events(
    device_id: Optional[str] = Query(None),
    _: bool = Depends(verify_api_key),
) -> List[Dict[str, Any]]:
    await demo_engine.initialize()
    return demo_engine.maintenance_events


@router.post("/maintenance/events", status_code=201, tags=["maintenance"])
async def create_maintenance_event(
    body: Dict[str, Any] = Body(...),
    _: bool = Depends(verify_api_key),
) -> Dict[str, Any]:
    await demo_engine.initialize()
    now = datetime.now(timezone.utc).isoformat()
    evt = {
        "id": f"maint-evt-{len(demo_engine.maintenance_events) + 1:03d}",
        "device_id": body.get("device_id", str(DEFAULT_DEMO_DEVICE_ID)),
        "event_type": body.get("event_type", "FILTER_REPLACEMENT"),
        "description": body.get("description", "Maintenance action recorded"),
        "initiated_by": body.get("initiated_by", "operator@aquanexis.local"),
        "performed_by": body.get("initiated_by", "operator@aquanexis.local"),
        "performed_at": now,
        "timestamp": now,
        "filter_instance_id": body.get("filter_instance_id"),
        "evidence": body.get("evidence") or {},
        "pre_maintenance_state": {"fhi": demo_engine.latest_filter_health.get("fhi")},
        "post_maintenance_state": {"fhi": 95},
        "pre_metrics": {"fhi": demo_engine.latest_filter_health.get("fhi") or 45},
        "post_metrics": {"fhi": 95},
        "notes": body.get("description"),
        "verified": True,
        "verification_status": "PASSED",
        "verification_data": {},
        "correlation_id": str(uuid4()),
        "created_at": now,
    }
    demo_engine.maintenance_events.insert(0, evt)
    return evt


@router.get("/maintenance/calibration/due", tags=["maintenance"])
async def get_calibration_due(
    device_id: Optional[str] = Query(None),
    _: bool = Depends(verify_api_key),
) -> List[Dict[str, Any]]:
    await demo_engine.initialize()
    now = datetime.now(timezone.utc)
    return [
        {
            "sensor_type": "tds",
            "sensor_id": "SEN-TDS-01",
            "status": "VALID",
            "last_calibration": (now - timedelta(days=20)).isoformat(),
            "next_due": (now + timedelta(days=70)).isoformat(),
            "days_overdue": None,
            "message": "Within 90-day calibration schedule",
        },
        {
            "sensor_type": "ph",
            "sensor_id": "SEN-PH-01",
            "status": "DUE_SOON",
            "last_calibration": (now - timedelta(days=82)).isoformat(),
            "next_due": (now + timedelta(days=8)).isoformat(),
            "days_overdue": None,
            "message": "2-point pH buffer calibration due in 8 days",
        },
        {
            "sensor_type": "turbidity",
            "sensor_id": "SEN-TURB-01",
            "status": "VALID",
            "last_calibration": (now - timedelta(days=35)).isoformat(),
            "next_due": (now + timedelta(days=55)).isoformat(),
            "days_overdue": None,
            "message": "Formazin NTU baseline verified",
        },
    ]


@router.get("/maintenance/calibration", tags=["maintenance"])
async def list_calibrations(
    device_id: Optional[str] = Query(None),
    _: bool = Depends(verify_api_key),
) -> List[Dict[str, Any]]:
    await demo_engine.initialize()
    return demo_engine.calibrations


@router.post("/maintenance/calibration", status_code=201, tags=["maintenance"])
async def create_calibration_record(
    body: Dict[str, Any] = Body(...),
    _: bool = Depends(verify_api_key),
) -> Dict[str, Any]:
    await demo_engine.initialize()
    now = datetime.now(timezone.utc)
    ref_val = float(body.get("reference_value") or 300.0)
    meas_val = float(body.get("measured_value") or 300.5)
    tol = float(body.get("tolerance") or 5.0)
    diff = abs(meas_val - ref_val)
    passed = diff <= tol
    rec = {
        "id": f"cal-rec-{len(demo_engine.calibrations) + 1:03d}",
        "device_id": body.get("device_id", str(DEFAULT_DEMO_DEVICE_ID)),
        "sensor_id": body.get("sensor_id", "SEN-TDS-01"),
        "sensor_type": body.get("sensor_type", "tds"),
        "calibration_method": body.get("calibration_method", "Standard Reference Buffer"),
        "reference_standard": body.get("reference_standard", "NIST Standard"),
        "reference_value": ref_val,
        "measured_value": meas_val,
        "tolerance": tol,
        "technician": body.get("technician") or "operator@aquanexis.local",
        "notes": body.get("notes"),
        "calibration_date": now.isoformat(),
        "correction_offset": round(ref_val - meas_val, 3),
        "result": "PASS" if passed else "OUT_OF_TOLERANCE",
        "next_calibration_due": (now + timedelta(days=90)).isoformat(),
        "calibration_state": "VALID" if passed else "OUT_OF_TOLERANCE",
        "created_at": now.isoformat(),
        "updated_at": now.isoformat(),
    }
    demo_engine.calibrations.insert(0, rec)
    return rec


@router.post("/maintenance/verification/start", status_code=201, tags=["maintenance"])
async def start_verification(
    body: Dict[str, Any] = Body(...),
    _: bool = Depends(verify_api_key),
) -> Dict[str, Any]:
    await demo_engine.initialize()
    now = datetime.now(timezone.utc).isoformat()
    vid = f"ver-run-{len(demo_engine.verifications) + 1:03d}"
    run = {
        "id": vid,
        "maintenance_event_id": body.get("maintenance_event_id", "maint-evt-001"),
        "device_id": body.get("device_id", str(DEFAULT_DEMO_DEVICE_ID)),
        "state": "PASSED",
        "started_at": now,
        "completed_at": now,
        "checks": [
            {
                "name": "Differential Pressure Reset (<50 kPa)",
                "passed": True,
                "value": 25.0,
                "threshold": 50.0,
            },
            {
                "name": "Permeate Flow Rate (>=1.5 L/min)",
                "passed": True,
                "value": 2.0,
                "threshold": 1.5,
            },
            {
                "name": "TDS Rejection Efficiency (>=90%)",
                "passed": True,
                "value": 95.5,
                "threshold": 90.0,
            },
            {"name": "Leak Contact Dry Check", "passed": True, "value": 0, "threshold": 0},
        ],
        "overall_result": True,
        "failure_reasons": [],
        "baseline_before": body.get("baseline_before") or {"dp_kpa": 175.0, "flow_lpm": 0.95},
        "baseline_after": {"dp_kpa": 25.0, "flow_lpm": 2.0},
        "created_at": now,
        "updated_at": now,
    }
    demo_engine.verifications[vid] = run
    return run


@router.get("/maintenance/verification/{verification_id}", tags=["maintenance"])
async def get_verification(
    verification_id: str,
    _: bool = Depends(verify_api_key),
) -> Dict[str, Any]:
    await demo_engine.initialize()
    if verification_id in demo_engine.verifications:
        return demo_engine.verifications[verification_id]
    for v in demo_engine.verifications.values():
        if v["maintenance_event_id"] == verification_id:
            return v
    return next(iter(demo_engine.verifications.values()))


@router.post("/maintenance/verification/{verification_id}/complete", tags=["maintenance"])
async def complete_verification(
    verification_id: str,
    body: Dict[str, Any] = Body(default={}),
    _: bool = Depends(verify_api_key),
) -> Dict[str, Any]:
    await demo_engine.initialize()
    run = demo_engine.verifications.get(verification_id) or next(
        iter(demo_engine.verifications.values())
    )
    run["state"] = "PASSED"
    run["overall_result"] = True
    run["completed_at"] = datetime.now(timezone.utc).isoformat()
    return run


@router.get("/maintenance/baseline/{device_id}", tags=["maintenance"])
async def get_active_baseline_version(
    device_id: str,
    _: bool = Depends(verify_api_key),
) -> Dict[str, Any]:
    await demo_engine.initialize()
    now = datetime.now(timezone.utc).isoformat()
    return {
        "id": "base-ver-001",
        "device_id": device_id,
        "version": 1,
        "maintenance_event_id": "maint-evt-001",
        "is_active": True,
        "metrics": {
            "flow_baseline_lpm": 2.0,
            "inlet_pressure_baseline_kpa": 310.0,
            "delta_p_baseline_kpa": 25.0,
            "tds_rejection_pct": 95.5,
        },
        "created_at": now,
        "activated_at": now,
    }


@router.get("/maintenance/recommendations", tags=["maintenance"])
async def get_maintenance_recommendations(
    device_id: Optional[str] = Query(None),
    _: bool = Depends(verify_api_key),
) -> List[Dict[str, Any]]:
    await demo_engine.initialize()
    return demo_engine.recommendations


# ── Notifications Endpoints ───────────────────────────────────────────────────


@router.get("/notifications", tags=["notifications"])
async def list_notifications(
    _: bool = Depends(verify_api_key),
) -> List[Dict[str, Any]]:
    await demo_engine.initialize()
    return demo_engine.notifications


@router.get("/notifications/stats", tags=["notifications"])
async def get_notification_stats(
    _: bool = Depends(verify_api_key),
) -> Dict[str, Any]:
    await demo_engine.initialize()
    sent = sum(1 for n in demo_engine.notifications if n["status"] == "sent")
    pending = sum(1 for n in demo_engine.notifications if n["status"] == "pending")
    return {
        "total_pending": pending,
        "total_processing": 0,
        "total_sent": sent,
        "total_retry": 0,
        "total_dead_letter": 0,
        "total_failed": 0,
    }


@router.get("/notifications/providers", tags=["notifications"])
async def list_notification_providers(
    _: bool = Depends(verify_api_key),
) -> List[Dict[str, Any]]:
    await demo_engine.initialize()
    return list(demo_engine.notification_providers.values())


@router.post("/notifications/providers", status_code=201, tags=["notifications"])
async def create_notification_provider(
    body: Dict[str, Any] = Body(...),
    _: bool = Depends(verify_api_key),
) -> Dict[str, Any]:
    await demo_engine.initialize()
    now = datetime.now(timezone.utc).isoformat()
    pid = f"prov-{len(demo_engine.notification_providers) + 1:03d}"
    cfg = {
        "id": pid,
        "device_id": body.get("device_id", str(DEFAULT_DEMO_DEVICE_ID)),
        "channel": body.get("channel", "email"),
        "provider": body.get("provider", "console"),
        "enabled": body.get("enabled", True),
        "config": body.get("config") or {},
        "min_severity": body.get("min_severity", "WARNING"),
        "alert_codes": body.get("alert_codes"),
        "rate_limit_per_hour": body.get("rate_limit_per_hour", 60),
        "created_at": now,
        "updated_at": now,
    }
    demo_engine.notification_providers[pid] = cfg
    return cfg


@router.get("/notifications/templates", tags=["notifications"])
async def list_notification_templates(
    _: bool = Depends(verify_api_key),
) -> List[Dict[str, Any]]:
    await demo_engine.initialize()
    return list(demo_engine.notification_templates.values())


@router.post("/notifications/test", tags=["notifications"])
async def test_notification(
    body: Dict[str, Any] = Body(...),
    _: bool = Depends(verify_api_key),
) -> Dict[str, Any]:
    await demo_engine.initialize()
    return {
        "success": True,
        "channel": body.get("channel", "email"),
        "recipient": body.get("recipient", "operator@aquanexis.local"),
        "error_category": None,
        "error_message": None,
        "provider_response": {"mode": "DEMO_MODE", "delivered_via": "console"},
    }


@router.get("/notifications/worker/stats", tags=["notifications"])
async def get_demo_worker_stats(
    _: bool = Depends(verify_api_key),
) -> Dict[str, Any]:
    await demo_engine.initialize()
    return {
        "running": True,
        "mode": "DEMO_MODE",
        "processed_count": len(demo_engine.notifications),
    }


# ── Safety Endpoints ──────────────────────────────────────────────────────────


@router.get("/safety/events/{device_id}", tags=["safety"])
async def get_safety_events(
    device_id: str,
    _: DeviceClaims = Depends(get_device_claims),
) -> List[Dict[str, Any]]:
    await demo_engine.initialize()
    return demo_engine.safety_events
