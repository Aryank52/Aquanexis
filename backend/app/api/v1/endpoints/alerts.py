"""
Alert API endpoints.
"""
from datetime import datetime, timedelta
from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select, desc, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database import get_db
from app.infrastructure.security import get_device_claims, verify_api_key, rate_limit
from app.infrastructure.logging import get_logger
from app.models.alert import Alert as AlertModel, AlertSeverity, AlertStatus
from app.models.device import Device as DeviceModel
from app.schemas.telemetry import (
    AlertResponse,
    AlertListQuery,
    AlertAcknowledgeRequest,
    AlertSnoozeRequest,
    AlertResolveRequest,
    AlertTransitionResponse,
    AlertSeverity as AlertSeveritySchema,
    AlertStatus as AlertStatusSchema,
)
from app.domain.alerts import Alert, ALERT_TRANSITIONS

logger = get_logger(__name__)

router = APIRouter(prefix="/alerts", tags=["alerts"])


def _alert_model_to_response(alert: AlertModel) -> AlertResponse:
    """Convert Alert model to response schema."""
    return AlertResponse(
        id=alert.id,
        device_id=alert.device_id,
        alert_code=alert.alert_code,
        severity=AlertSeveritySchema(alert.severity.value),
        status=AlertStatusSchema(alert.status.value),
        title=alert.title,
        message=alert.message,
        trigger_source=alert.trigger_source,
        trigger_value=alert.trigger_value,
        threshold_value=alert.threshold_value,
        evidence=alert.evidence or {},
        created_at=alert.created_at,
        acknowledged_at=alert.acknowledged_at,
        snoozed_until=alert.snoozed_until,
        resolved_at=alert.resolved_at,
        auto_cleared_at=alert.auto_cleared_at,
        created_by=alert.created_by,
        acknowledged_by=alert.acknowledged_by,
        resolved_by=alert.resolved_by,
    )


@router.get("", response_model=List[AlertResponse])
async def list_alerts(
    device_id: Optional[UUID] = Query(None),
    alert_code: Optional[str] = Query(None),
    severity: Optional[AlertSeveritySchema] = Query(None),
    status: Optional[AlertStatusSchema] = Query(None),
    start: Optional[datetime] = Query(None),
    end: Optional[datetime] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    device_claims = Depends(get_device_claims),
):
    """List alerts with filtering and pagination."""
    # Build query
    query = select(AlertModel)
    
    # Device filtering: device can only see own alerts unless admin
    # For now, allow all authenticated devices to query
    if device_id:
        query = query.where(AlertModel.device_id == device_id)
    elif device_claims:
        # Filter by device's own alerts if not admin
        query = query.where(AlertModel.device_id == device_claims.device_id)
    
    if alert_code:
        query = query.where(AlertModel.alert_code == alert_code)
    if severity:
        query = query.where(AlertModel.severity == AlertSeverity(severity.value))
    if status:
        query = query.where(AlertModel.status == AlertStatus(status.value))
    if start:
        query = query.where(AlertModel.created_at >= start)
    if end:
        query = query.where(AlertModel.created_at <= end)
    
    query = query.order_by(desc(AlertModel.created_at)).limit(limit).offset(offset)
    
    result = await db.execute(query)
    alerts = result.scalars().all()
    
    return [_alert_model_to_response(a) for a in alerts]


@router.get("/{alert_id}", response_model=AlertResponse)
async def get_alert(
    alert_id: UUID,
    db: AsyncSession = Depends(get_db),
    device_claims = Depends(get_device_claims),
):
    """Get a single alert by ID."""
    alert = await db.get(AlertModel, alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    # Check authorization: device can only access own alerts
    if device_claims and alert.device_id != device_claims.device_id:
        raise HTTPException(status_code=403, detail="Not authorized to access this alert")
    
    return _alert_model_to_response(alert)


@router.post("/{alert_id}/acknowledge", response_model=AlertTransitionResponse)
async def acknowledge_alert(
    alert_id: UUID,
    request: AlertAcknowledgeRequest,
    db: AsyncSession = Depends(get_db),
    device_claims = Depends(get_device_claims),
):
    """Acknowledge an alert."""
    alert = await db.get(AlertModel, alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    # Check authorization
    if device_claims and alert.device_id != device_claims.device_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Check if already acknowledged or resolved
    if alert.status in (AlertStatus.RESOLVED, AlertStatus.AUTO_CLEARED):
        raise HTTPException(
            status_code=400, 
            detail=f"Cannot acknowledge alert in {alert.status.value} state"
        )
    
    if alert.status == AlertStatus.ACKNOWLEDGED:
        return AlertTransitionResponse(
            success=False,
            alert=_alert_model_to_response(alert),
            message="Alert already acknowledged"
        )
    
    # Validate transition using domain logic
    domain_alert = Alert(
        id=alert.id,
        device_id=alert.device_id,
        alert_code=alert.alert_code,
        severity=alert.severity,
        status=alert.status,
    )
    
    if not domain_alert.can_transition_to(AlertStatus.ACKNOWLEDGED):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid transition from {alert.status.value} to acknowledged"
        )
    
    # Perform transition
    user = request.user or (str(device_claims.device_id) if device_claims else "system")
    alert.status = AlertStatus.ACKNOWLEDGED
    alert.acknowledged_at = datetime.utcnow()
    alert.acknowledged_by = user
    
    await db.commit()
    await db.refresh(alert)
    
    logger.info(
        "alert_acknowledged",
        alert_id=str(alert_id),
        user=user
    )
    
    return AlertTransitionResponse(
        success=True,
        alert=_alert_model_to_response(alert),
        message="Alert acknowledged"
    )


@router.post("/{alert_id}/snooze", response_model=AlertTransitionResponse)
async def snooze_alert(
    alert_id: UUID,
    request: AlertSnoozeRequest,
    db: AsyncSession = Depends(get_db),
    device_claims = Depends(get_device_claims),
):
    """Snooze an alert for a specified duration."""
    alert = await db.get(AlertModel, alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    # Check authorization
    if device_claims and alert.device_id != device_claims.device_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    if alert.status in (AlertStatus.RESOLVED, AlertStatus.AUTO_CLEARED):
        raise HTTPException(
            status_code=400,
            detail=f"Cannot snooze alert in {alert.status.value} state"
        )
    
    # Validate transition
    domain_alert = Alert(
        id=alert.id,
        device_id=alert.device_id,
        alert_code=alert.alert_code,
        severity=alert.severity,
        status=alert.status,
    )
    
    if not domain_alert.can_transition_to(AlertStatus.SNOOZED):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid transition from {alert.status.value} to snoozed"
        )
    
    # Perform transition
    user = request.user or (str(device_claims.device_id) if device_claims else "system")
    snoozed_until = datetime.utcnow() + timedelta(minutes=request.duration_minutes)
    
    alert.status = AlertStatus.SNOOZED
    alert.snoozed_until = snoozed_until
    alert.acknowledged_by = user
    
    await db.commit()
    await db.refresh(alert)
    
    logger.info(
        "alert_snoozed",
        alert_id=str(alert_id),
        duration_minutes=request.duration_minutes,
        user=user
    )
    
    return AlertTransitionResponse(
        success=True,
        alert=_alert_model_to_response(alert),
        message=f"Alert snoozed for {request.duration_minutes} minutes"
    )


@router.post("/{alert_id}/resolve", response_model=AlertTransitionResponse)
async def resolve_alert(
    alert_id: UUID,
    request: AlertResolveRequest,
    db: AsyncSession = Depends(get_db),
    device_claims = Depends(get_device_claims),
):
    """Resolve an alert."""
    alert = await db.get(AlertModel, alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    # Check authorization
    if device_claims and alert.device_id != device_claims.device_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    if alert.status in (AlertStatus.RESOLVED, AlertStatus.AUTO_CLEARED):
        return AlertTransitionResponse(
            success=False,
            alert=_alert_model_to_response(alert),
            message=f"Alert already {alert.status.value}"
        )
    
    # Validate transition
    domain_alert = Alert(
        id=alert.id,
        device_id=alert.device_id,
        alert_code=alert.alert_code,
        severity=alert.severity,
        status=alert.status,
    )
    
    if not domain_alert.can_transition_to(AlertStatus.RESOLVED):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid transition from {alert.status.value} to resolved"
        )
    
    # Perform transition
    user = request.user or (str(device_claims.device_id) if device_claims else "system")
    
    alert.status = AlertStatus.RESOLVED
    alert.resolved_at = datetime.utcnow()
    alert.resolved_by = user
    
    await db.commit()
    await db.refresh(alert)
    
    logger.info(
        "alert_resolved",
        alert_id=str(alert_id),
        user=user
    )
    
    return AlertTransitionResponse(
        success=True,
        alert=_alert_model_to_response(alert),
        message="Alert resolved"
    )


@router.get("/summary/counts")
async def get_alert_counts(
    device_id: Optional[UUID] = Query(None),
    db: AsyncSession = Depends(get_db),
    device_claims = Depends(get_device_claims),
):
    """Get alert counts by status and severity."""
    query = select(AlertModel)
    
    if device_id:
        query = query.where(AlertModel.device_id == device_id)
    elif device_claims:
        query = query.where(AlertModel.device_id == device_claims.device_id)
    
    result = await db.execute(query)
    alerts = result.scalars().all()
    
    counts = {
        "total": len(alerts),
        "by_status": {},
        "by_severity": {},
    }
    
    for alert in alerts:
        # By status
        status_key = alert.status.value
        counts["by_status"][status_key] = counts["by_status"].get(status_key, 0) + 1
        
        # By severity
        severity_key = alert.severity.value
        counts["by_severity"][severity_key] = counts["by_severity"].get(severity_key, 0) + 1
    
    return counts