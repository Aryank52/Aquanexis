"""
Safety domain models - pure Python, no framework dependencies.
"""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any, List
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


class SafetyValidationResult(str, Enum):
    """Result of safety validation."""
    VALID = "valid"
    INVALID = "invalid"
    INSUFFICIENT_DATA = "insufficient_data"
    COOLDOWN_ACTIVE = "cooldown_active"
    SENSOR_FAULT = "sensor_fault"


@dataclass
class SafetyConfig:
    """Safety configuration for a device."""
    # Leak protection
    leak_action: str = "close_inlet_valve"  # close_inlet_valve, stop_pump, both
    leak_validate_with: List[str] = field(default_factory=lambda: ["flow_delta", "pressure_drop"])
    leak_cooldown_sec: int = 300
    leak_persistence_readings: int = 2

    # Pressure protection
    pressure_max_kpa: float = 600.0
    pressure_action: str = "open_relief_valve"  # open_relief_valve, stop_pump
    pressure_cooldown_sec: int = 60
    pressure_min_kpa: float = 50.0
    pressure_action_low: str = "stop_pump"

    # Flow protection
    flow_min_lpm: float = 0.1
    dry_run_action: str = "stop_pump"
    dry_run_cooldown_sec: int = 120
    flow_unstable_threshold_pct: float = 30.0  # % deviation from baseline

    # Energy protection
    pump_current_max_a: float = 2.5
    overcurrent_action: str = "stop_pump"
    overcurrent_cooldown_sec: int = 180
    pump_power_max_w: float = 500.0

    # Validation
    persistence_required_readings: int = 2
    cooldown_enabled: bool = True


@dataclass
class SafetyValidationContext:
    """Context for safety validation."""
    device_id: UUID
    timestamp: datetime
    current_reading: Dict[str, Any]
    previous_readings: List[Dict[str, Any]]
    device_config: Dict[str, Any]
    safety_config: Dict[str, Any]
    device_status: str


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
    action_id: UUID = field(default_factory=uuid4)
    device_id: UUID
    action_type: SafetyActionType
    event_type: SafetyEventType
    trigger_value: float
    threshold_value: float
    evidence: Dict[str, Any]
    status: SafetyActionStatus = SafetyActionStatus.PENDING
    created_at: datetime = field(default_factory=datetime.utcnow)
    executed_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    firmware_response: Optional[Dict[str, Any]] = None


@dataclass
class SafetyEvent:
    """Record of a safety event."""
    event_id: UUID = field(default_factory=uuid4)
    device_id: UUID
    event_type: SafetyEventType
    severity: str  # INFO, WARNING, CRITICAL
    trigger_value: float
    threshold_value: float
    evidence: Dict[str, Any]
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
    status: str  # dry, suspect, leak_confirmed


@dataclass
class PressureDiagnostics:
    """Pressure diagnostics."""
    current_kpa: float
    trend_1h: float
    trend_24h: float
    fouling_indicator: float  # 0-1, higher = more fouling
    pump_curve_deviation: float  # % deviation from expected
    delta_pressure_kpa: Optional[float] = None
    delta_pressure_baseline_kpa: Optional[float] = None
    status: Literal["normal", "elevated", "critical"]


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
    status: Literal["normal", "low", "high", "unstable"]


@dataclass
class PumpDiagnostics:
    """Pump energy diagnostics."""
    current_a: float
    power_w: Optional[float] = None
    efficiency_trend: float  # % change over 7d
    runtime_hours: float
    starts_count: int
    current_baseline_a: Optional[float] = None
    efficiency_baseline: Optional[float] = None
    status: Literal["normal", "degraded", "overcurrent", "offline"]


@dataclass
class TankDiagnostics:
    """Tank state diagnostics."""
    level_percent: float
    fill_rate_lpm: Optional[float] = None
    empty_rate_lpm: Optional[float] = None
    stagnation_hours: float
    status: Literal["normal", "filling", "draining", "stagnant", "empty"]


@dataclass
class LeakDiagnostics:
    """Leak detection diagnostics."""
    leak_detected: bool
    leak_probability: float  # 0-1
    flow_delta_lpm: float
    pressure_drop_kpa: float
    sensor_state: bool
    persistence_readings: int
    status: Literal["dry", "suspect", "leak_confirmed"]


@dataclass
class PressureDiagnostics:
    """Pressure diagnostics."""
    current_kpa: float
    trend_1h: float
    trend_24h: float
    fouling_indicator: float  # 0-1, higher = more fouling
    pump_curve_deviation: float  # % deviation from expected
    status: Literal["normal", "elevated", "critical"]


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
    status: Literal["normal", "low", "high", "unstable"]


@dataclass
class TankDiagnostics:
    """Tank state diagnostics."""
    level_percent: float
    fill_rate_lpm: Optional[float] = None
    empty_rate_lpm: Optional[float] = None
    stagnation_hours: float
    status: Literal["normal", "filling", "draining", "stagnant", "empty"]


@dataclass
class PumpDiagnostics:
    """Pump energy diagnostics."""
    current_a: float
    power_w: Optional[float] = None
    efficiency_trend: float  # % change over 7d
    runtime_hours: float
    starts_count: int
    status: Literal["normal", "degraded", "overcurrent", "offline"]


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
    overall_status: Literal["healthy", "degraded", "critical"]
    calculation_version: str = "1.0"


@dataclass
class SafetyActionCommand:
    """Command to execute a safety action on firmware."""
    command_id: UUID = field(default_factory=uuid4)
    device_id: UUID
    action_type: SafetyActionType
    event_type: SafetyEventType
    trigger_value: float
    threshold_value: float
    timestamp: datetime = field(default_factory=datetime.utcnow)
    timeout_sec: int = 5
    # Signature for firmware validation
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
class SafetyConfig:
    """Safety configuration for a device."""
    # Leak protection
    leak_action: str = "close_inlet_valve"
    leak_validate_with: List[str] = field(default_factory=lambda: ["flow_delta", "pressure_drop"])
    leak_cooldown_sec: int = 300
    leak_persistence_readings: int = 2

    # Pressure protection
    pressure_max_kpa: float = 600.0
    pressure_action: str = "open_relief_valve"
    pressure_cooldown_sec: int = 60
    pressure_min_kpa: float = 50.0
    pressure_action_low: str = "stop_pump"

    # Flow protection
    flow_min_lpm: float = 0.1
    dry_run_action: str = "stop_pump"
    dry_run_cooldown_sec: int = 120
    flow_unstable_threshold_pct: float = 30.0

    # Energy protection
    pump_current_max_a: float = 2.5
    overcurrent_action: str = "stop_pump"
    overcurrent_cooldown_sec: int = 180
    pump_power_max_w: float = 500.0

    # Validation
    persistence_required_readings: int = 2
    cooldown_enabled: bool = True


@dataclass
class SafetyActionCommand:
    """Command to execute a safety action on firmware."""
    command_id: UUID = field(default_factory=uuid4)
    device_id: UUID
    action_type: SafetyActionType
    event_type: SafetyEventType
    trigger_value: float
    threshold_value: float
    timestamp: datetime = field(default_factory=datetime.utcnow)
    timeout_sec: int = 5
    # Signature for firmware validation
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
    cooldown_by_code: Dict[str, int] = field(default_factory=lambda: {
        "leak_detected": 120,
        "pressure_high": 60,
        "pressure_low": 60,
        "flow_low": 30,
        "flow_interrupted": 120,
        "pump_overcurrent": 120,
        "water_quality_degraded": 60,
        "filter_stress_high": 120,
        "filter_health_critical": 180,
        "pressure_high": 60,
        "pump_overcurrent": 120,
        "tank_level_low": 30,
    })


# Firmware command protocol
@dataclass
class FirmwareCommand:
    """Command sent to firmware."""
    command_id: UUID = field(default_factory=uuid4)
    device_id: UUID
    command_type: str  # "safety_action", "config_update", "calibration", "reset"
    payload: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.utcnow)
    signature: str = ""  # HMAC signature for validation
    sequence: int = 0


@dataclass
class FirmwareResponse:
    """Response from firmware."""
    command_id: UUID
    device_id: UUID
    status: str  # "success", "error", "timeout"
    response_data: Dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    signature: str = ""  # HMAC signature for validation


# Safety audit event
@dataclass
class SafetyAuditEvent:
    """Audit log entry for safety actions."""
    event_id: UUID = field(default_factory=uuid4)
    device_id: UUID
    event_type: str  # "safety_action", "validation", "config_change"
    action_type: Optional[str] = None
    event_type: str = ""  # SafetyEventType value
    trigger_value: Optional[float] = None
    threshold_value: Optional[float] = None
    action_taken: Optional[str] = None
    action_status: Optional[str] = None
    trigger_value: Optional[float] = None
    threshold_value: Optional[float] = None
    evidence: Dict[str, Any] = field(default_factory=dict)
    firmware_response: Optional[Dict[str, Any]] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    initiated_by: str = "system"  # "system", "user", "scheduled"
    user_id: Optional[str] = None