"""
Maintenance and Lifecycle domain models - pure Python, no framework dependencies.
"""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any, List
from uuid import UUID, uuid4


class FilterCategory(str, Enum):
    """Filter component categories."""
    SEDIMENT = "sediment"
    PRE_CARBON = "pre_carbon"
    ACTIVATED_CARBON_BLOCK = "activated_carbon_block"
    RO_MEMBRANE = "ro_membrane"
    UF_MEMBRANE = "uf_membrane"
    UV_CHAMBER = "uv_chamber"
    UV_LAMP = "uv_lamp"
    POST_CARBON = "post_carbon"
    MINERAL_REMINERALIZATION = "mineral_remineralization"
    ALKALINE_TREATMENT = "alkaline_treatment"
    OTHER = "other"


class CompatibilityResult(str, Enum):
    """Filter compatibility check results."""
    COMPATIBLE = "compatible"
    INCOMPATIBLE = "incompatible"
    REQUIRES_REVIEW = "requires_review"
    INSUFFICIENT_INFORMATION = "insufficient_information"


class FilterLifecycleState(str, Enum):
    """Installed filter lifecycle states."""
    AVAILABLE = "available"
    INSTALLED = "installed"
    MAINTENANCE_DUE = "maintenance_due"
    DEGRADED = "degraded"
    REMOVED = "removed"
    REPLACEMENT_PENDING = "replacement_pending"
    VERIFICATION_PENDING = "verification_pending"


class MaintenanceEventType(str, Enum):
    """Types of maintenance events."""
    INSTALL = "install"
    REPLACE = "replace"
    INSPECT = "inspect"
    CLEAN = "clean"
    RECALIBRATE = "recalibrate"
    VERIFY = "verify"
    REMOVE = "remove"


class MaintenanceWorkflowState(str, Enum):
    """Maintenance workflow states."""
    REQUESTED = "requested"
    APPROVED = "approved"
    IN_PROGRESS = "in_progress"
    AWAITING_VERIFICATION = "awaiting_verification"
    VERIFIED = "verified"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class CalibrationState(str, Enum):
    """Calibration status states."""
    VALID = "valid"
    DUE_SOON = "due_soon"
    DUE = "due"
    OVERDUE = "overdue"
    FAILED = "failed"
    UNKNOWN = "unknown"


class VerificationState(str, Enum):
    """Post-maintenance verification states."""
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    INCOMPLETE = "incomplete"


# Valid maintenance workflow transitions
MAINTENANCE_WORKFLOW_TRANSITIONS = {
    MaintenanceWorkflowState.REQUESTED: [
        MaintenanceWorkflowState.APPROVED,
        MaintenanceWorkflowState.CANCELLED,
    ],
    MaintenanceWorkflowState.APPROVED: [
        MaintenanceWorkflowState.IN_PROGRESS,
        MaintenanceWorkflowState.CANCELLED,
    ],
    MaintenanceWorkflowState.IN_PROGRESS: [
        MaintenanceWorkflowState.AWAITING_VERIFICATION,
        MaintenanceWorkflowState.FAILED,
        MaintenanceWorkflowState.CANCELLED,
    ],
    MaintenanceWorkflowState.AWAITING_VERIFICATION: [
        MaintenanceWorkflowState.VERIFIED,
        MaintenanceWorkflowState.FAILED,
    ],
    MaintenanceWorkflowState.VERIFIED: [
        MaintenanceWorkflowState.COMPLETED,
    ],
    MaintenanceWorkflowState.COMPLETED: [],
    MaintenanceWorkflowState.FAILED: [
        MaintenanceWorkflowState.REQUESTED,
    ],
    MaintenanceWorkflowState.CANCELLED: [
        MaintenanceWorkflowState.REQUESTED,
    ],
}


@dataclass
class FilterCatalog:
    """Filter catalog entry."""
    id: UUID = field(default_factory=uuid4)
    filter_identifier: str = ""  # Unique filter identifier
    manufacturer: str = ""
    product_name: str = ""
    category: FilterCategory = FilterCategory.OTHER
    purifier_compatibility: List[str] = field(default_factory=list)  # Purifier model IDs
    stage_position: int = 0
    specifications: Dict[str, Any] = field(default_factory=dict)
    connector_details: Optional[str] = None
    dimensions_mm: Optional[Dict[str, float]] = None
    rated_service_interval_days: Optional[int] = None
    rated_usage_volume_liters: Optional[float] = None
    installation_requirements: Optional[str] = None
    maintenance_instructions: Optional[str] = None
    datasheet_reference: Optional[str] = None
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class InstalledFilter:
    """Installed filter instance tracking."""
    id: UUID = field(default_factory=uuid4)
    device_id: UUID = field(default_factory=uuid4)
    catalog_id: UUID = field(default_factory=uuid4)
    stage_position: int = 0
    installation_date: datetime = field(default_factory=datetime.utcnow)
    installer: Optional[str] = None
    serial_number: Optional[str] = None
    batch_identifier: Optional[str] = None
    cumulative_volume_liters: float = 0.0
    operating_hours: float = 0.0
    lifecycle_state: FilterLifecycleState = FilterLifecycleState.AVAILABLE
    previous_installation_id: Optional[UUID] = None
    removal_date: Optional[datetime] = None
    replacement_reason: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class MaintenanceEvent:
    """Maintenance event record."""
    id: UUID = field(default_factory=uuid4)
    device_id: UUID = field(default_factory=uuid4)
    filter_instance_id: Optional[UUID] = None
    event_type: MaintenanceEventType = MaintenanceEventType.INSPECT
    timestamp: datetime = field(default_factory=datetime.utcnow)
    initiated_by: Optional[str] = None
    description: str = ""
    pre_maintenance_state: Dict[str, Any] = field(default_factory=dict)
    post_maintenance_state: Dict[str, Any] = field(default_factory=dict)
    evidence: Dict[str, Any] = field(default_factory=dict)
    verification_status: Optional[VerificationState] = None
    correlation_id: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class MaintenanceWorkflow:
    """Maintenance workflow with state machine."""
    id: UUID = field(default_factory=uuid4)
    device_id: UUID = field(default_factory=uuid4)
    maintenance_event_id: UUID = field(default_factory=uuid4)
    state: MaintenanceWorkflowState = MaintenanceWorkflowState.REQUESTED
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    failed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def can_transition_to(self, new_state: MaintenanceWorkflowState) -> bool:
        """Check if transition to new_state is valid."""
        return new_state in MAINTENANCE_WORKFLOW_TRANSITIONS.get(self.state, [])

    def transition_to(self, new_state: MaintenanceWorkflowState) -> bool:
        """Attempt to transition to new state. Returns True if successful."""
        if not self.can_transition_to(new_state):
            return False
        
        self.state = new_state
        now = datetime.utcnow()
        
        if new_state == MaintenanceWorkflowState.IN_PROGRESS:
            self.started_at = now
        elif new_state in (MaintenanceWorkflowState.COMPLETED, MaintenanceWorkflowState.VERIFIED):
            self.completed_at = now
        elif new_state == MaintenanceWorkflowState.FAILED:
            self.failed_at = now
        
        self.updated_at = now
        return True


@dataclass
class CalibrationRecord:
    """Calibration record for sensors."""
    id: UUID = field(default_factory=uuid4)
    device_id: UUID = field(default_factory=uuid4)
    sensor_id: str = ""
    sensor_type: str = ""  # tds, ph, turbidity, temperature, flow, pressure, level
    calibration_date: datetime = field(default_factory=datetime.utcnow)
    calibration_method: str = ""
    reference_standard: str = ""
    reference_value: float = 0.0
    measured_value: float = 0.0
    correction_offset: float = 0.0
    tolerance: float = 0.0
    result: str = ""  # PASS, FAIL, ADJUSTED
    technician: Optional[str] = None
    notes: Optional[str] = None
    next_calibration_due: Optional[datetime] = None
    calibration_state: CalibrationState = CalibrationState.UNKNOWN
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class CalibrationPolicy:
    """Calibration due tracking policy per sensor."""
    id: UUID = field(default_factory=uuid4)
    device_id: UUID = field(default_factory=uuid4)
    sensor_id: str = ""
    sensor_type: str = ""
    time_interval_days: Optional[int] = None
    usage_interval_measurements: Optional[int] = None
    usage_interval_volume_liters: Optional[float] = None
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class VerificationRun:
    """Post-maintenance verification run."""
    id: UUID = field(default_factory=uuid4)
    maintenance_event_id: UUID = field(default_factory=uuid4)
    device_id: UUID = field(default_factory=uuid4)
    state: VerificationState = VerificationState.PENDING
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    checks: List["VerificationCheck"] = field(default_factory=list)
    overall_result: Optional[bool] = None
    failure_reasons: List[str] = field(default_factory=list)
    baseline_before: Optional[Dict[str, Any]] = None
    baseline_after: Optional[Dict[str, Any]] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class VerificationCheck:
    """Individual verification check."""
    name: str
    description: str
    expected_range: Dict[str, float]  # min, max
    actual_value: Optional[float] = None
    passed: Optional[bool] = None
    check_type: str = "measured"  # measured, unavailable, simulated, manual
    evidence: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BaselineVersion:
    """Baseline versioning for before/after maintenance comparison."""
    id: UUID = field(default_factory=uuid4)
    device_id: UUID = field(default_factory=uuid4)
    version: int = 1
    maintenance_event_id: Optional[UUID] = None
    is_active: bool = True
    metrics: Dict[str, Any] = field(default_factory=dict)  # flow, pressure, delta_p, etc.
    created_at: datetime = field(default_factory=datetime.utcnow)
    activated_at: Optional[datetime] = None


@dataclass
class MaintenanceRecommendation:
    """Maintenance recommendation with evidence."""
    device_id: UUID = field(default_factory=uuid4)
    filter_instance_id: Optional[UUID] = None
    trigger: str = ""  # time_based, usage_based, health_based, calibration_due
    severity: str = "info"  # info, warning, critical
    evidence: Dict[str, Any] = field(default_factory=dict)
    urgency_days: Optional[int] = None
    recommended_action: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)
    acknowledged_at: Optional[datetime] = None
    dismissed_at: Optional[datetime] = None


# Default calibration policies per sensor type
DEFAULT_CALIBRATION_POLICIES = {
    "tds": {"time_days": 90, "usage_measurements": 10000},
    "ph": {"time_days": 30, "usage_measurements": 5000},
    "turbidity": {"time_days": 90, "usage_measurements": 10000},
    "temperature": {"time_days": 365, "usage_measurements": 50000},
    "flow": {"time_days": 180, "usage_measurements": 20000},
    "pressure": {"time_days": 180, "usage_measurements": 20000},
    "level": {"time_days": 365, "usage_measurements": 50000},
}