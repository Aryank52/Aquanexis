"""
Alert domain models - pure Python, no framework dependencies.
"""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any
from uuid import UUID, uuid4


class AlertSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class AlertStatus(str, Enum):
    DETECTED = "detected"
    OPEN = "open"
    ACKNOWLEDGED = "acknowledged"
    SNOOZED = "snoozed"
    RESOLVED = "resolved"
    AUTO_CLEARED = "auto_cleared"


# Valid state transitions
ALERT_TRANSITIONS = {
    AlertStatus.DETECTED: [AlertStatus.OPEN, AlertStatus.AUTO_CLEARED],
    AlertStatus.OPEN: [AlertStatus.ACKNOWLEDGED, AlertStatus.SNOOZED, AlertStatus.RESOLVED, AlertStatus.AUTO_CLEARED],
    AlertStatus.ACKNOWLEDGED: [AlertStatus.SNOOZED, AlertStatus.RESOLVED, AlertStatus.AUTO_CLEARED],
    AlertStatus.SNOOZED: [AlertStatus.OPEN, AlertStatus.RESOLVED, AlertStatus.AUTO_CLEARED],
    AlertStatus.RESOLVED: [],  # Terminal state
    AlertStatus.AUTO_CLEARED: [],  # Terminal state
}


@dataclass
class Alert:
    """Alert entity with full lifecycle."""
    id: UUID = field(default_factory=uuid4)
    device_id: UUID = field(default_factory=uuid4)
    alert_code: str = ""
    severity: AlertSeverity = AlertSeverity.INFO
    status: AlertStatus = AlertStatus.DETECTED
    title: str = ""
    message: str = ""
    trigger_source: str = ""
    trigger_value: Optional[float] = None
    threshold_value: Optional[float] = None
    evidence: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    acknowledged_at: Optional[datetime] = None
    snoozed_until: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    auto_cleared_at: Optional[datetime] = None
    created_by: Optional[str] = None
    resolved_by: Optional[str] = None

    def can_transition_to(self, new_status: AlertStatus) -> bool:
        """Check if transition to new_status is valid."""
        return new_status in ALERT_TRANSITIONS.get(self.status, [])

    def transition_to(self, new_status: AlertStatus, user: Optional[str] = None) -> bool:
        """Attempt to transition to new status. Returns True if successful."""
        if not self.can_transition_to(new_status):
            return False
        
        self.status = new_status
        now = datetime.utcnow()
        
        if new_status == AlertStatus.ACKNOWLEDGED:
            self.acknowledged_at = now
            self.acknowledged_by = user
        elif new_status == AlertStatus.SNOOZED:
            # snoozed_until should be set externally
            pass
        elif new_status == AlertStatus.RESOLVED:
            self.resolved_at = now
            self.resolved_by = user
        elif new_status == AlertStatus.AUTO_CLEARED:
            self.auto_cleared_at = now
        
        return True

    def is_active(self) -> bool:
        """Check if alert is in an active state requiring attention."""
        return self.status in (AlertStatus.DETECTED, AlertStatus.OPEN, AlertStatus.ACKNOWLEDGED, AlertStatus.SNOOZED)

    def is_terminal(self) -> bool:
        """Check if alert is in a terminal state."""
        return self.status in (AlertStatus.RESOLVED, AlertStatus.AUTO_CLEARED)


@dataclass
class AlertRule:
    """Rule for automatic alert generation."""
    code: str
    name: str
    severity: AlertSeverity
    description: str
    # Function that evaluates the rule given device data
    # Returns (should_trigger, trigger_value, threshold_value, evidence)
    evaluate: callable = field(default=None)
    # Optional: auto-clear when condition is no longer met
    auto_clear: bool = False
    # Optional: cooldown period in seconds
    cooldown_seconds: int = 300


# Built-in alert codes
ALERT_CODES = {
    # Water quality
    "water_quality_degraded": {"severity": AlertSeverity.WARNING, "auto_clear": True},
    "water_quality_critical": {"severity": AlertSeverity.CRITICAL, "auto_clear": True},
    
    # Filter health
    "filter_stress_high": {"severity": AlertSeverity.WARNING, "auto_clear": True},
    "filter_health_critical": {"severity": AlertSeverity.CRITICAL, "auto_clear": False},
    "filter_rul_low": {"severity": AlertSeverity.WARNING, "auto_clear": True},
    "filter_rul_critical": {"severity": AlertSeverity.CRITICAL, "auto_clear": False},
    
    # System diagnostics
    "leak_detected": {"severity": AlertSeverity.CRITICAL, "auto_clear": False},
    "leak_persistent": {"severity": AlertSeverity.CRITICAL, "auto_clear": False},
    "pressure_low": {"severity": AlertSeverity.WARNING, "auto_clear": True},
    "pressure_high": {"severity": AlertSeverity.CRITICAL, "auto_clear": True},
    "pressure_unstable": {"severity": AlertSeverity.WARNING, "auto_clear": True},
    "pressure_differential_high": {"severity": AlertSeverity.WARNING, "auto_clear": True},
    "flow_low": {"severity": AlertSeverity.WARNING, "auto_clear": True},
    "flow_high": {"severity": AlertSeverity.WARNING, "auto_clear": True},
    "flow_interrupted": {"severity": AlertSeverity.CRITICAL, "auto_clear": True},
    "flow_unstable": {"severity": AlertSeverity.WARNING, "auto_clear": True},
    "tank_level_low": {"severity": AlertSeverity.WARNING, "auto_clear": True},
    
    # Pump
    "pump_dry_run_risk": {"severity": AlertSeverity.CRITICAL, "auto_clear": True},
    "pump_excessive_runtime": {"severity": AlertSeverity.WARNING, "auto_clear": True},
    "pump_overcurrent": {"severity": AlertSeverity.CRITICAL, "auto_clear": True},
    "pump_abnormal_power": {"severity": AlertSeverity.WARNING, "auto_clear": True},
    
    # Sensors
    "sensor_missing": {"severity": AlertSeverity.WARNING, "auto_clear": True},
    "sensor_stuck": {"severity": AlertSeverity.WARNING, "auto_clear": True},
    "sensor_impossible_value": {"severity": AlertSeverity.WARNING, "auto_clear": True},
    "sensor_rapid_change": {"severity": AlertSeverity.WARNING, "auto_clear": True},
    "sensor_calibration_due": {"severity": AlertSeverity.INFO, "auto_clear": True},
    "sensor_calibration_overdue": {"severity": AlertSeverity.WARNING, "auto_clear": True},
    
    # Device
    "device_offline": {"severity": AlertSeverity.WARNING, "auto_clear": True},
    "device_reconnected": {"severity": AlertSeverity.INFO, "auto_clear": True},
    
    # Maintenance
    "maintenance_due": {"severity": AlertSeverity.INFO, "auto_clear": True},
    "maintenance_overdue": {"severity": AlertSeverity.WARNING, "auto_clear": False},
}