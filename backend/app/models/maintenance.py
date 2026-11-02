"""
Maintenance and Lifecycle database models.
"""
import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    Column, DateTime, Enum, ForeignKey, Index, String, Text, JSON, 
    Integer, Float, Boolean, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.infrastructure.database import Base


class FilterCategory(str, enum.Enum):
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


class FilterLifecycleState(str, enum.Enum):
    AVAILABLE = "available"
    INSTALLED = "installed"
    MAINTENANCE_DUE = "maintenance_due"
    DEGRADED = "degraded"
    REMOVED = "removed"
    REPLACEMENT_PENDING = "replacement_pending"
    VERIFICATION_PENDING = "verification_pending"


class MaintenanceEventType(str, enum.Enum):
    INSTALL = "install"
    REPLACE = "replace"
    INSPECT = "inspect"
    CLEAN = "clean"
    RECALIBRATE = "recalibrate"
    VERIFY = "verify"
    REMOVE = "remove"


class MaintenanceWorkflowState(str, enum.Enum):
    REQUESTED = "requested"
    APPROVED = "approved"
    IN_PROGRESS = "in_progress"
    AWAITING_VERIFICATION = "awaiting_verification"
    VERIFIED = "verified"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class CalibrationState(str, enum.Enum):
    VALID = "valid"
    DUE_SOON = "due_soon"
    DUE = "due"
    OVERDUE = "overdue"
    FAILED = "failed"
    UNKNOWN = "unknown"


class VerificationState(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    INCOMPLETE = "incomplete"


class FilterCatalogModel(Base):
    """Filter catalog - centralized filter definitions."""
    __tablename__ = "filter_catalog"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    filter_identifier = Column(String(128), nullable=False, unique=True, index=True)
    manufacturer = Column(String(128), nullable=False)
    product_name = Column(String(128), nullable=False)
    category = Column(Enum(FilterCategory), nullable=False)
    purifier_compatibility = Column(JSONB, nullable=False, default=list)  # List of purifier model IDs
    stage_position = Column(Integer, nullable=False, default=0)
    specifications = Column(JSONB, nullable=False, default=dict)
    connector_details = Column(Text, nullable=True)
    dimensions_mm = Column(JSONB, nullable=True)  # {"length": x, "diameter": y}
    rated_service_interval_days = Column(Integer, nullable=True)
    rated_usage_volume_liters = Column(Float, nullable=True)
    installation_requirements = Column(Text, nullable=True)
    maintenance_instructions = Column(Text, nullable=True)
    datasheet_reference = Column(String(256), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True, index=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("ix_filter_catalog_category_active", "category", "is_active"),
    )


class InstalledFilterModel(Base):
    """Installed filter instance tracking."""
    __tablename__ = "installed_filters"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    device_id = Column(UUID(as_uuid=True), ForeignKey("devices.id", ondelete="CASCADE"), nullable=False, index=True)
    catalog_id = Column(UUID(as_uuid=True), ForeignKey("filter_catalog.id", ondelete="SET NULL"), nullable=False, index=True)
    stage_position = Column(Integer, nullable=False)
    installation_date = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    installer = Column(String(128), nullable=True)
    serial_number = Column(String(128), nullable=True)
    batch_identifier = Column(String(128), nullable=True)
    cumulative_volume_liters = Column(Float, nullable=False, default=0.0)
    operating_hours = Column(Float, nullable=False, default=0.0)
    lifecycle_state = Column(Enum(FilterLifecycleState), nullable=False, default=FilterLifecycleState.AVAILABLE, index=True)
    previous_installation_id = Column(UUID(as_uuid=True), ForeignKey("installed_filters.id"), nullable=True)
    removal_date = Column(DateTime(timezone=True), nullable=True)
    replacement_reason = Column(String(128), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        # Note: postgresql_where not supported in UniqueConstraint, using application-level check
        Index("ix_installed_filters_device_state", "device_id", "lifecycle_state"),
        Index("ix_installed_filters_catalog", "catalog_id"),
        Index("ix_installed_filters_device_stage", "device_id", "stage_position"),
    )


class MaintenanceEventModel(Base):
    """Maintenance event record."""
    __tablename__ = "maintenance_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    device_id = Column(UUID(as_uuid=True), ForeignKey("devices.id", ondelete="CASCADE"), nullable=False, index=True)
    filter_instance_id = Column(UUID(as_uuid=True), ForeignKey("installed_filters.id", ondelete="SET NULL"), nullable=True, index=True)
    event_type = Column(Enum(MaintenanceEventType), nullable=False, index=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    initiated_by = Column(String(128), nullable=True)
    description = Column(Text, nullable=False)
    pre_maintenance_state = Column(JSONB, nullable=False, default=dict)
    post_maintenance_state = Column(JSONB, nullable=False, default=dict)
    evidence = Column(JSONB, nullable=False, default=dict)
    verification_status = Column(String(16), nullable=True)  # VerificationState value
    correlation_id = Column(String(64), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    __table_args__ = (
        Index("ix_maintenance_events_device_type", "device_id", "event_type"),
        Index("ix_maintenance_events_timestamp", "timestamp"),
    )


class MaintenanceWorkflowModel(Base):
    """Maintenance workflow with state machine."""
    __tablename__ = "maintenance_workflows"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    device_id = Column(UUID(as_uuid=True), ForeignKey("devices.id", ondelete="CASCADE"), nullable=False, index=True)
    maintenance_event_id = Column(UUID(as_uuid=True), ForeignKey("maintenance_events.id", ondelete="CASCADE"), nullable=False, index=True)
    state = Column(Enum(MaintenanceWorkflowState), nullable=False, default=MaintenanceWorkflowState.REQUESTED, index=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    failed_at = Column(DateTime(timezone=True), nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("ix_maintenance_workflows_device_state", "device_id", "state"),
    )


class CalibrationRecordModel(Base):
    """Calibration record for sensors."""
    __tablename__ = "calibration_records"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    device_id = Column(UUID(as_uuid=True), ForeignKey("devices.id", ondelete="CASCADE"), nullable=False, index=True)
    sensor_id = Column(String(64), nullable=False, index=True)
    sensor_type = Column(String(32), nullable=False, index=True)  # tds, ph, turbidity, temperature, flow, pressure, level
    calibration_date = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    calibration_method = Column(String(64), nullable=False)
    reference_standard = Column(String(128), nullable=False)
    reference_value = Column(Float, nullable=False)
    measured_value = Column(Float, nullable=False)
    correction_offset = Column(Float, nullable=False, default=0.0)
    tolerance = Column(Float, nullable=False)
    result = Column(String(16), nullable=False)  # PASS, FAIL, ADJUSTED
    technician = Column(String(128), nullable=True)
    notes = Column(Text, nullable=True)
    next_calibration_due = Column(DateTime(timezone=True), nullable=True)
    calibration_state = Column(Enum(CalibrationState), nullable=False, default=CalibrationState.UNKNOWN, index=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("ix_calibration_records_device_type", "device_id", "sensor_type"),
        Index("ix_calibration_records_due", "next_calibration_due", "calibration_state"),
    )


class CalibrationPolicyModel(Base):
    """Calibration due tracking policy per sensor."""
    __tablename__ = "calibration_policies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    device_id = Column(UUID(as_uuid=True), ForeignKey("devices.id", ondelete="CASCADE"), nullable=False, index=True)
    sensor_id = Column(String(64), nullable=False)
    sensor_type = Column(String(32), nullable=False)
    time_interval_days = Column(Integer, nullable=True)
    usage_interval_measurements = Column(Integer, nullable=True)
    usage_interval_volume_liters = Column(Float, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True, index=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("ix_calibration_policies_device_type", "device_id", "sensor_type"),
    )


class VerificationRunModel(Base):
    """Post-maintenance verification run."""
    __tablename__ = "verification_runs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    maintenance_event_id = Column(UUID(as_uuid=True), ForeignKey("maintenance_events.id", ondelete="CASCADE"), nullable=False, index=True)
    device_id = Column(UUID(as_uuid=True), ForeignKey("devices.id", ondelete="CASCADE"), nullable=False, index=True)
    state = Column(Enum(VerificationState), nullable=False, default=VerificationState.PENDING, index=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    checks = Column(JSONB, nullable=False, default=list)  # List of VerificationCheck dicts
    overall_result = Column(Boolean, nullable=True)
    failure_reasons = Column(JSONB, nullable=False, default=list)
    baseline_before = Column(JSONB, nullable=True)
    baseline_after = Column(JSONB, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("ix_verification_runs_device_state", "device_id", "state"),
    )


class BaselineVersionModel(Base):
    """Baseline versioning for before/after maintenance comparison."""
    __tablename__ = "baseline_versions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    device_id = Column(UUID(as_uuid=True), ForeignKey("devices.id", ondelete="CASCADE"), nullable=False, index=True)
    version = Column(Integer, nullable=False, default=1)
    maintenance_event_id = Column(UUID(as_uuid=True), ForeignKey("maintenance_events.id", ondelete="SET NULL"), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True, index=True)
    metrics = Column(JSONB, nullable=False, default=dict)  # flow, pressure, delta_p, etc.
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    activated_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        UniqueConstraint("device_id", "version", name="uq_device_baseline_version"),
        Index("ix_baseline_versions_device_active", "device_id", "is_active"),
    )


class MaintenanceRecommendationModel(Base):
    """Maintenance recommendations."""
    __tablename__ = "maintenance_recommendations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    device_id = Column(UUID(as_uuid=True), ForeignKey("devices.id", ondelete="CASCADE"), nullable=False, index=True)
    filter_instance_id = Column(UUID(as_uuid=True), ForeignKey("installed_filters.id", ondelete="SET NULL"), nullable=True)
    trigger = Column(String(32), nullable=False)  # time_based, usage_based, health_based, calibration_due
    severity = Column(String(16), nullable=False, default="info")  # info, warning, critical
    evidence = Column(JSONB, nullable=False, default=dict)
    urgency_days = Column(Integer, nullable=True)
    recommended_action = Column(String(256), nullable=False)
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)
    dismissed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    __table_args__ = (
        Index("ix_maintenance_recommendations_device_severity", "device_id", "severity"),
    )