"""
Alert State Machine Service - Enforces valid state transitions with audit logging.
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from fastapi import Depends
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.alerts import ALERT_TRANSITIONS, Alert
from app.domain.alerts import AlertSeverity as DomainAlertSeverity
from app.domain.alerts import AlertStatus as DomainAlertStatus
from app.infrastructure.database import get_db
from app.infrastructure.logging import get_logger
from app.models.alert import Alert as AlertModel
from app.models.alert import AlertStatus

logger = get_logger(__name__)


class TransitionResult(Enum):
    """Result of a state transition attempt."""

    SUCCESS = "success"
    INVALID_TRANSITION = "invalid_transition"
    NOT_FOUND = "not_found"
    UNAUTHORIZED = "unauthorized"
    ALREADY_IN_STATE = "already_in_state"
    TERMINAL_STATE = "terminal_state"


@dataclass
class TransitionOutcome:
    """Outcome of a transition operation."""

    result: TransitionResult
    alert: Optional[AlertModel] = None
    message: str = ""
    previous_status: Optional[AlertStatus] = None
    new_status: Optional[AlertStatus] = None


class AlertStateMachine:
    """
    Service that enforces the alert state machine.
    Validates transitions, logs audit trail, and handles auto-clearing.
    """

    # Define which alert codes support auto-clearing
    AUTO_CLEAR_CODES = {
        "water_quality_degraded",
        "water_quality_critical",
        "filter_stress_high",
        "filter_rul_low",
        "pressure_low",
        "pressure_high",
        "pressure_unstable",
        "pressure_differential_high",
        "flow_low",
        "flow_high",
        "flow_interrupted",
        "flow_unstable",
        "tank_level_low",
        "pump_dry_run_risk",
        "pump_excessive_runtime",
        "pump_overcurrent",
        "pump_abnormal_power",
        "sensor_missing",
        "sensor_stuck",
        "sensor_impossible_value",
        "sensor_rapid_change",
        "sensor_calibration_due",
        "sensor_calibration_overdue",
        "device_offline",
        "device_reconnected",
        "maintenance_due",
    }

    # Codes that should NOT auto-clear (require manual intervention)
    MANUAL_ONLY_CODES = {
        "filter_health_critical",
        "filter_rul_critical",
        "leak_detected",
        "leak_persistent",
        "maintenance_overdue",
    }

    def __init__(self, db: AsyncSession):
        self.db = db

    def _to_domain_status(self, status: AlertStatus) -> DomainAlertStatus:
        """Convert model enum to domain enum."""
        return DomainAlertStatus(status.value)

    def _to_model_status(self, status: DomainAlertStatus) -> AlertStatus:
        """Convert domain enum to model enum."""
        return AlertStatus(status.value)

    def can_transition(self, alert: AlertModel, new_status: AlertStatus) -> Tuple[bool, str]:
        """
        Check if a transition is valid.
        Returns (is_valid, reason_if_invalid).
        """
        current_domain = self._to_domain_status(alert.status)
        new_domain = self._to_domain_status(new_status)

        # Check if already in the target state
        if alert.status == new_status:
            return False, f"Alert already in {new_status.value} state"

        # Check if in terminal state
        if current_domain in (DomainAlertStatus.RESOLVED, DomainAlertStatus.AUTO_CLEARED):
            return False, f"Cannot transition from terminal state {alert.status.value}"

        # Check valid transitions
        valid_targets = ALERT_TRANSITIONS.get(current_domain, [])
        if new_domain not in valid_targets:
            return False, f"Invalid transition from {alert.status.value} to {new_status.value}"

        return True, ""

    async def transition(
        self,
        alert_id: UUID,
        new_status: AlertStatus,
        user: Optional[str] = None,
        snoozed_until: Optional[datetime] = None,
    ) -> TransitionOutcome:
        """
        Execute a state transition with full validation and audit logging.
        """
        # Fetch alert
        alert = await self.db.get(AlertModel, alert_id)
        if not alert:
            return TransitionOutcome(
                result=TransitionResult.NOT_FOUND,
                message=f"Alert {alert_id} not found",
            )

        # Validate transition
        is_valid, reason = self.can_transition(alert, new_status)
        if not is_valid:
            return TransitionOutcome(
                result=TransitionResult.INVALID_TRANSITION,
                alert=alert,
                message=reason,
                previous_status=alert.status,
                new_status=new_status,
            )

        # Store previous state for audit
        previous_status = alert.status

        # Perform transition
        domain_alert = Alert(
            id=alert.id,
            device_id=alert.device_id,
            alert_code=alert.alert_code,
            severity=DomainAlertSeverity(alert.severity.value),
            status=self._to_domain_status(alert.status),
        )

        success = domain_alert.transition_to(self._to_domain_status(new_status), user)
        if not success:
            return TransitionOutcome(
                result=TransitionResult.INVALID_TRANSITION,
                alert=alert,
                message="Domain transition failed",
                previous_status=previous_status,
                new_status=new_status,
            )

        # Update model
        alert.status = new_status
        now = datetime.now(timezone.utc)

        if new_status == AlertStatus.ACKNOWLEDGED:
            alert.acknowledged_at = now
            alert.acknowledged_by = user
        elif new_status == AlertStatus.SNOOZED:
            alert.snoozed_until = snoozed_until
            alert.acknowledged_by = user
        elif new_status == AlertStatus.RESOLVED:
            alert.resolved_at = now
            alert.resolved_by = user
        elif new_status == AlertStatus.AUTO_CLEARED:
            alert.auto_cleared_at = now

        await self.db.commit()
        await self.db.refresh(alert)

        # Audit log
        logger.info(
            "alert_transition",
            alert_id=str(alert_id),
            device_id=str(alert.device_id),
            alert_code=alert.alert_code,
            previous_status=previous_status.value,
            new_status=new_status.value,
            user=user,
        )

        return TransitionOutcome(
            result=TransitionResult.SUCCESS,
            alert=alert,
            message=f"Transitioned from {previous_status.value} to {new_status.value}",
            previous_status=previous_status,
            new_status=new_status,
        )

    async def auto_clear_if_applicable(
        self,
        alert: AlertModel,
        current_condition_met: bool,
    ) -> Optional[TransitionOutcome]:
        """
        Auto-clear alert if condition is no longer met and alert supports auto-clear.
        Returns transition outcome if auto-cleared, None otherwise.
        """
        # Only auto-clear if:
        # 1. Alert code supports auto-clear
        # 2. Alert is in an active state
        # 3. Condition is no longer met (current_condition_met = False)
        if alert.alert_code not in self.AUTO_CLEAR_CODES:
            return None

        if alert.status in (AlertStatus.RESOLVED, AlertStatus.AUTO_CLEARED):
            return None

        if current_condition_met:
            # Condition still met, don't auto-clear
            return None

        # Auto-clear the alert
        return await self.transition(
            alert_id=alert.id,
            new_status=AlertStatus.AUTO_CLEARED,
            user="system_auto_clear",
        )

    async def get_alert_with_device_check(
        self,
        alert_id: UUID,
        device_id: Optional[UUID] = None,
    ) -> Optional[AlertModel]:
        """Get alert and verify device ownership."""
        alert = await self.db.get(AlertModel, alert_id)
        if not alert:
            return None

        if device_id and alert.device_id != device_id:
            return None

        return alert

    async def bulk_transition(
        self,
        alert_ids: List[UUID],
        new_status: AlertStatus,
        user: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Perform bulk transition on multiple alerts.
        Returns summary of results.
        """
        results = {
            "success": [],
            "failed": [],
            "total": len(alert_ids),
        }

        for alert_id in alert_ids:
            outcome = await self.transition(alert_id, new_status, user)
            if outcome.result == TransitionResult.SUCCESS:
                results["success"].append(str(alert_id))
            else:
                results["failed"].append(
                    {
                        "alert_id": str(alert_id),
                        "reason": outcome.message,
                    }
                )

        return results

    async def check_and_auto_clear_alerts(
        self,
        device_id: UUID,
        alert_code: str,
        condition_met: bool,
    ) -> List[TransitionOutcome]:
        """
        Check all active alerts of a specific code for a device and auto-clear if applicable.
        Used by evaluation engine when a condition is no longer met.
        """
        if alert_code not in self.AUTO_CLEAR_CODES:
            return []

        # Find active alerts of this code for this device
        query = select(AlertModel).where(
            and_(
                AlertModel.device_id == device_id,
                AlertModel.alert_code == alert_code,
                AlertModel.status.in_(
                    [
                        AlertStatus.DETECTED,
                        AlertStatus.OPEN,
                        AlertStatus.ACKNOWLEDGED,
                        AlertStatus.SNOOZED,
                    ]
                ),
            )
        )

        result = await self.db.execute(query)
        alerts = result.scalars().all()

        outcomes = []
        for alert in alerts:
            outcome = await self.auto_clear_if_applicable(alert, condition_met)
            if outcome:
                outcomes.append(outcome)

        return outcomes


# Dependency injection helper
async def get_alert_state_machine(
    db: AsyncSession = Depends(get_db),
) -> AlertStateMachine:
    return AlertStateMachine(db)
