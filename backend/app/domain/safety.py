"""
Safety domain models - pure Python, no framework dependencies.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Literal, Optional
from uuid import UUID, uuid4


class SafetyActionType(str, Enum):
    """Types of safety actions that can be executed."""

    CLOSE_INLET_VALVE = "close_inlet_valve"
    STOP_PUMP = "stop_pump"
    OPEN_RELIEF_VALVE = "open_relief_valve"
    BOTH_VALVE_AND_PUMP = "both_valve_and_pump"


class SafetyEventType(str, Enum):
    """Types of safety events that can trigger actions."""

    LEAK_DETECTED = "leak_detected"
    OVERPRESSURE = "overpressure"
    DRY_RUN = "dry_run"
    OVERCURRENT = "overcurrent"


class SafetyActionStatus(str, Enum):
    """Status of a safety action execution."""

    PENDING = "pending"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    VALIDATION_FAILED = "validation_failed"
    COOLDOWN_ACTIVE = "cooldown_active"


@dataclass
class SafetyConfig:
    """Safety configuration for a device."""

    leak_action: str = "close_inlet_valve"
    leak_validate_with: List[str] = field(default_factory=lambda: ["flow_delta", "pressure_drop"])
    leak_cooldown_sec: int = 300
    leak_persistence_readings: int = 2

    pressure_max_kpa: float = 600.0
    pressure_action: str = "open_relief_valve"
    pressure_cooldown_sec: int = 60
    pressure_min_kpa: float = 50.0
    pressure_action_low: str = "stop_pump"

    flow_min_lpm: float = 0.1
    dry_run_action: str = "stop_pump"
    dry_run_cooldown_sec: int = 120
    flow_unstable_threshold_pct: float = 30.0

    pump_current_max_a: float = 2.5
    overcurrent_action: str = "stop_pump"
    overcurrent_cooldown_sec: int = 180
    pump_power_max_w: float = 500.0

    persistence_required_readings: int = 2
    cooldown_enabled: bool = True
    cooldown_by_code: Dict[str, int] = field(
        default_factory=lambda: {
            "leak_detected": 120,
            "pressure_high": 60,
            "pressure_low": 60,
            "flow_low": 30,
            "flow_interrupted": 120,
            "pump_overcurrent": 120,
            "water_quality_degraded": 60,
            "filter_stress_high": 120,
            "filter_health_critical": 180,
            "tank_level_low": 30,
        }
    )


@dataclass
class SafetyValidationContext:
    """Context for safety validation."""

    device_id: UUID
    timestamp: datetime
    current_reading: Dict[str, Any]
    previous_readings: List[Dict[str, Any]]
    device_config: Dict[str, Any] = field(default_factory=dict)
    safety_config: Dict[str, Any] = field(default_factory=dict)
    device_status: str = "active"


@dataclass
class SafetyValidationResult:
    """Result of safety validation."""

    event_type: str
    is_valid: bool
    validation_result: str  # VALID, INVALID, INSUFFICIENT_DATA, COOLDOWN_ACTIVE, SENSOR_FAULT
    trigger_value: Optional[float] = None
    threshold_value: Optional[float] = None
    evidence: Dict[str, Any] = field(default_factory=dict)
    cooldown_remaining_sec: Optional[int] = None
    recommended_action: Optional[str] = None


@dataclass
class SafetyAction:
    """A safety action to be executed."""

    device_id: UUID = field(default_factory=uuid4)
    action_type: SafetyActionType = SafetyActionType.CLOSE_INLET_VALVE
    event_type: SafetyEventType = SafetyEventType.LEAK_DETECTED
    trigger_value: float = 0.0
    threshold_value: float = 0.0
    evidence: Dict[str, Any] = field(default_factory=dict)
    action_id: UUID = field(default_factory=uuid4)
    status: SafetyActionStatus = SafetyActionStatus.PENDING
    created_at: datetime = field(default_factory=datetime.utcnow)
    executed_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    firmware_response: Optional[Dict[str, Any]] = None


@dataclass
class SafetyEvent:
    """Record of a safety event."""

    device_id: UUID = field(default_factory=uuid4)
    event_type: SafetyEventType = SafetyEventType.LEAK_DETECTED
    severity: str = "CRITICAL"
    trigger_value: float = 0.0
    threshold_value: float = 0.0
    evidence: Dict[str, Any] = field(default_factory=dict)
    event_id: UUID = field(default_factory=uuid4)
    action_taken: Optional[str] = None
    action_status: Optional[SafetyActionStatus] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[str] = None


@dataclass
class LeakDiagnostics:
    """Leak detection diagnostics."""

    leak_detected: bool
    leak_probability: float  # 0-1
    flow_delta_lpm: float
    pressure_drop_kpa: float
    sensor_state: bool
    persistence_readings: int
    status: str = "dry"  # dry, suspect, leak_confirmed


@dataclass
class PressureDiagnostics:
    """Pressure diagnostics."""

    current_kpa: float
    trend_1h: float
    trend_24h: float
    fouling_indicator: float  # 0-1, higher = more fouling
    pump_curve_deviation: float = 0.0  # % deviation from expected
    delta_pressure_kpa: Optional[float] = None
    delta_pressure_baseline_kpa: Optional[float] = None
    status: Literal["normal", "elevated", "critical"] = "normal"


@dataclass
class FlowDiagnostics:
    """Flow diagnostics."""

    current_lpm: float
    trend_1h: float
    trend_24h: float
    recovery_ratio: Optional[float] = None
    permeate_flow: Optional[float] = None
    reject_flow: Optional[float] = None
    baseline_lpm: Optional[float] = None
    deviation_pct: Optional[float] = None
    status: Literal["normal", "low", "high", "unstable"] = "normal"


@dataclass
class PumpDiagnostics:
    """Pump energy diagnostics."""

    current_a: float
    power_w: Optional[float] = None
    efficiency_trend: float = 0.0  # % change over 7d
    runtime_hours: float = 0.0
    starts_count: int = 0
    current_baseline_a: Optional[float] = None
    efficiency_baseline: Optional[float] = None
    status: Literal["normal", "degraded", "overcurrent", "offline"] = "normal"


@dataclass
class TankDiagnostics:
    """Tank state diagnostics."""

    level_percent: float
    fill_rate_lpm: Optional[float] = None
    empty_rate_lpm: Optional[float] = None
    stagnation_hours: float = 0.0
    status: Literal["normal", "filling", "draining", "stagnant", "empty"] = "normal"


@dataclass
class SystemDiagnostics:
    """Aggregated system diagnostics."""

    device_id: UUID
    timestamp: datetime
    pressure: PressureDiagnostics
    flow: FlowDiagnostics
    leak: LeakDiagnostics
    tank: TankDiagnostics
    pump: PumpDiagnostics
    overall_status: Literal["healthy", "degraded", "critical"] = "healthy"
    calculation_version: str = "1.0"


@dataclass
class SafetyActionCommand:
    """Command to execute a safety action on firmware."""

    device_id: UUID = field(default_factory=uuid4)
    action_type: SafetyActionType = SafetyActionType.CLOSE_INLET_VALVE
    event_type: SafetyEventType = SafetyEventType.LEAK_DETECTED
    trigger_value: float = 0.0
    threshold_value: float = 0.0
    command_id: UUID = field(default_factory=uuid4)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    timeout_sec: int = 5
    signature: Optional[str] = None


@dataclass
class SafetyActionResponse:
    """Response from firmware after safety action execution."""

    command_id: UUID
    device_id: UUID
    action_type: SafetyActionType
    status: SafetyActionStatus
    executed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    firmware_response: Optional[Dict[str, Any]] = None


@dataclass
class FirmwareCommand:
    """Command sent to firmware."""

    device_id: UUID = field(default_factory=uuid4)
    command_type: str = "safety_action"
    payload: Dict[str, Any] = field(default_factory=dict)
    command_id: UUID = field(default_factory=uuid4)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    signature: str = ""
    sequence: int = 0


@dataclass
class FirmwareResponse:
    """Response from firmware."""

    command_id: UUID
    device_id: UUID
    status: str
    response_data: Dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    signature: str = ""


@dataclass
class SafetyAuditEvent:
    """Audit log entry for safety actions."""

    device_id: UUID = field(default_factory=uuid4)
    event_type: str = "safety_action"
    event_id: UUID = field(default_factory=uuid4)
    action_type: Optional[str] = None
    trigger_value: Optional[float] = None
    threshold_value: Optional[float] = None
    action_taken: Optional[str] = None
    action_status: Optional[str] = None
    evidence: Dict[str, Any] = field(default_factory=dict)
    firmware_response: Optional[Dict[str, Any]] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    initiated_by: str = "system"
    user_id: Optional[str] = None
