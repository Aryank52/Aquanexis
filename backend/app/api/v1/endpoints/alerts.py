"""
Alert API endpoints.
"""

from datetime import datetime, timedelta, timezone
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.alerts import ALERT_TRANSITIONS
from app.infrastructure.database import get_db
from app.infrastructure.logging import get_logger
from app.infrastructure.security import get_device_claims
from app.models.alert import Alert as AlertModel
from app.models.alert import AlertSeverity, AlertStatus
from app.schemas.telemetry import (
    AlertAcknowledgeRequest,
    AlertResolveRequest,
    AlertResponse,
    AlertSnoozeRequest,
    AlertTransitionResponse,
)
from app.schemas.telemetry import (
    AlertSeverity as AlertSeveritySchema,
)
from app.schemas.telemetry import (
    AlertStatus as AlertStatusSchema,
)
from app.services.alert_state_machine import (
    AlertStateMachine,
    TransitionResult,
    get_alert_state_machine,
)

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
    device_claims=Depends(get_device_claims),
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
    device_claims=Depends(get_device_claims),
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
    device_claims=Depends(get_device_claims),
    state_machine: AlertStateMachine = Depends(get_alert_state_machine),
):
    """Acknowledge an alert using the state machine."""
    user = request.user or (str(device_claims.device_id) if device_claims else "system")

    outcome = await state_machine.transition(
        alert_id=alert_id,
        new_status=AlertStatus.ACKNOWLEDGED,
        user=user,
    )

    if outcome.result == TransitionResult.NOT_FOUND:
        raise HTTPException(status_code=404, detail="Alert not found")
    elif outcome.result == TransitionResult.UNAUTHORIZED:
        raise HTTPException(status_code=403, detail="Not authorized")
    elif outcome.result in (
        TransitionResult.INVALID_TRANSITION,
        TransitionResult.ALREADY_IN_STATE,
        TransitionResult.TERMINAL_STATE,
    ):
        # Return the current alert state with error message
        return AlertTransitionResponse(
            success=False,
            alert=_alert_model_to_response(outcome.alert),
            message=outcome.message,
        )

    return AlertTransitionResponse(
        success=True,
        alert=_alert_model_to_response(outcome.alert),
        message=outcome.message,
    )


@router.post("/{alert_id}/snooze", response_model=AlertTransitionResponse)
async def snooze_alert(
    alert_id: UUID,
    request: AlertSnoozeRequest,
    db: AsyncSession = Depends(get_db),
    device_claims=Depends(get_device_claims),
    state_machine: AlertStateMachine = Depends(get_alert_state_machine),
):
    """Snooze an alert for a specified duration using the state machine."""
    user = request.user or (str(device_claims.device_id) if device_claims else "system")
    snoozed_until = datetime.now(timezone.utc) + timedelta(minutes=request.duration_minutes)

    outcome = await state_machine.transition(
        alert_id=alert_id,
        new_status=AlertStatus.SNOOZED,
        user=user,
        snoozed_until=snoozed_until,
    )

    if outcome.result == TransitionResult.NOT_FOUND:
        raise HTTPException(status_code=404, detail="Alert not found")
    elif outcome.result == TransitionResult.UNAUTHORIZED:
        raise HTTPException(status_code=403, detail="Not authorized")
    elif outcome.result in (
        TransitionResult.INVALID_TRANSITION,
        TransitionResult.ALREADY_IN_STATE,
        TransitionResult.TERMINAL_STATE,
    ):
        return AlertTransitionResponse(
            success=False,
            alert=_alert_model_to_response(outcome.alert),
            message=outcome.message,
        )

    return AlertTransitionResponse(
        success=True,
        alert=_alert_model_to_response(outcome.alert),
        message=f"Alert snoozed for {request.duration_minutes} minutes",
    )


@router.post("/{alert_id}/resolve", response_model=AlertTransitionResponse)
async def resolve_alert(
    alert_id: UUID,
    request: AlertResolveRequest,
    db: AsyncSession = Depends(get_db),
    device_claims=Depends(get_device_claims),
    state_machine: AlertStateMachine = Depends(get_alert_state_machine),
):
    """Resolve an alert using the state machine."""
    user = request.user or (str(device_claims.device_id) if device_claims else "system")

    outcome = await state_machine.transition(
        alert_id=alert_id,
        new_status=AlertStatus.RESOLVED,
        user=user,
    )

    if outcome.result == TransitionResult.NOT_FOUND:
        raise HTTPException(status_code=404, detail="Alert not found")
    elif outcome.result == TransitionResult.UNAUTHORIZED:
        raise HTTPException(status_code=403, detail="Not authorized")
    elif outcome.result in (
        TransitionResult.INVALID_TRANSITION,
        TransitionResult.ALREADY_IN_STATE,
        TransitionResult.TERMINAL_STATE,
    ):
        return AlertTransitionResponse(
            success=False,
            alert=_alert_model_to_response(outcome.alert),
            message=outcome.message,
        )

    return AlertTransitionResponse(
        success=True,
        alert=_alert_model_to_response(outcome.alert),
        message=outcome.message,
    )


@router.get("/summary/counts")
async def get_alert_counts(
    device_id: Optional[UUID] = Query(None),
    db: AsyncSession = Depends(get_db),
    device_claims=Depends(get_device_claims),
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


@router.get("/{alert_id}/valid-transitions")
async def get_valid_transitions(
    alert_id: UUID,
    db: AsyncSession = Depends(get_db),
    device_claims=Depends(get_device_claims),
):
    """Get valid state transitions for an alert based on current state."""
    alert = await db.get(AlertModel, alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    # Check authorization
    if device_claims and alert.device_id != device_claims.device_id:
        raise HTTPException(status_code=403, detail="Not authorized")

    # Get valid transitions from domain logic
    domain_status = AlertStatus(alert.status.value)
    # Map to domain enum
    from app.domain.alerts import AlertStatus as DomainAlertStatus

    domain_enum = DomainAlertStatus(alert.status.value)
    valid_targets = ALERT_TRANSITIONS.get(domain_enum, [])

    return {
        "alert_id": str(alert_id),
        "current_status": alert.status.value,
        "valid_transitions": [s.value for s in valid_targets],
        "is_terminal": alert.status in (AlertStatus.RESOLVED, AlertStatus.AUTO_CLEARED),
    }


@router.post("/bulk-transition", response_model=dict)
async def bulk_transition_alerts(
    alert_ids: List[UUID],
    new_status: AlertStatusSchema,
    user: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    state_machine: AlertStateMachine = Depends(get_alert_state_machine),
    device_claims=Depends(get_device_claims),
):
    """Perform bulk transition on multiple alerts (admin only)."""
    # In a real implementation, add admin check here
    # if not device_claims.is_admin: raise HTTPException(403)

    outcome = await state_machine.bulk_transition(
        alert_ids=alert_ids,
        new_status=AlertStatus(new_status.value),
        user=user or "bulk_operation",
    )

    return {
        "success_count": len(outcome["success"]),
        "failed_count": len(outcome["failed"]),
        "total": outcome["total"],
        "success": outcome["success"],
        "failed": outcome["failed"],
    }


@router.post("/auto-clear-check")
async def check_auto_clear(
    device_id: UUID,
    alert_code: str,
    condition_met: bool,
    db: AsyncSession = Depends(get_db),
    state_machine: AlertStateMachine = Depends(get_alert_state_machine),
    device_claims=Depends(get_device_claims),
):
    """
    Check and auto-clear alerts for a device/alert_code if condition is no longer met.
    This endpoint is called by the evaluation engine when a condition resolves.
    """
    # Verify device access
    if device_claims and device_claims.device_id != device_id:
        raise HTTPException(status_code=403, detail="Not authorized for this device")

    outcomes = await state_machine.check_and_auto_clear_alerts(
        device_id=device_id,
        alert_code=alert_code,
        condition_met=condition_met,
    )

    return {
        "device_id": str(device_id),
        "alert_code": alert_code,
        "condition_met": condition_met,
        "auto_cleared_count": len(outcomes),
        "cleared_alerts": [
            str(o.alert.id) for o in outcomes if o.result == TransitionResult.SUCCESS
        ],
    }
