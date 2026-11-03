"""
Maintenance Pydantic schemas for API requests/responses.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field

# Re-export enums
from app.domain.maintenance import (
    CalibrationState,
    CompatibilityResult,
    FilterCategory,
    FilterLifecycleState,
    MaintenanceEventType,
    MaintenanceWorkflowState,
    VerificationState,
)

# ===== Filter Catalog Schemas =====


class FilterCatalogBase(BaseModel):
    filter_identifier: str = Field(..., min_length=1, max_length=128)
    manufacturer: str = Field(..., min_length=1, max_length=128)
    product_name: str = Field(..., min_length=1, max_length=128)
    category: FilterCategory
    purifier_compatibility: List[str] = Field(default_factory=list)
    stage_position: int = Field(..., ge=1)
    specifications: Dict[str, Any] = Field(default_factory=dict)
    connector_details: Optional[str] = None
    dimensions_mm: Optional[Dict[str, float]] = None
    rated_service_interval_days: Optional[int] = Field(None, ge=1)
    rated_usage_volume_liters: Optional[float] = Field(None, ge=0)
    installation_requirements: Optional[str] = None
    maintenance_instructions: Optional[str] = None
    datasheet_reference: Optional[str] = None


class FilterCatalogCreate(FilterCatalogBase):
    pass


class FilterCatalogUpdate(BaseModel):
    manufacturer: Optional[str] = Field(None, max_length=128)
    product_name: Optional[str] = Field(None, max_length=128)
    category: Optional[FilterCategory] = None
    purifier_compatibility: Optional[List[str]] = None
    stage_position: Optional[int] = Field(None, ge=1)
    specifications: Optional[Dict[str, Any]] = None
    connector_details: Optional[str] = None
    dimensions_mm: Optional[Dict[str, float]] = None
    rated_service_interval_days: Optional[int] = Field(None, ge=1)
    rated_usage_volume_liters: Optional[float] = Field(None, ge=0)
    installation_requirements: Optional[str] = None
    maintenance_instructions: Optional[str] = None
    datasheet_reference: Optional[str] = None
    is_active: Optional[bool] = None


class FilterCatalogResponse(FilterCatalogBase):
    id: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ===== Installed Filter Schemas =====


class InstalledFilterBase(BaseModel):
    device_id: UUID
    catalog_id: UUID
    stage_position: int
    installer: Optional[str] = None
    serial_number: Optional[str] = None
    batch_identifier: Optional[str] = None
    lifecycle_state: FilterLifecycleState


class InstalledFilterInstall(BaseModel):
    catalog_id: UUID
    stage_position: int = Field(..., ge=1)
    installer: Optional[str] = None
    serial_number: Optional[str] = None
    batch_identifier: Optional[str] = None


class InstalledFilterReplace(BaseModel):
    stage_position: int = Field(..., ge=1)
    new_catalog_id: UUID
    installer: Optional[str] = None
    serial_number: Optional[str] = None
    batch_identifier: Optional[str] = None
    replacement_reason: Optional[str] = None


class InstalledFilterResponse(InstalledFilterBase):
    id: UUID
    cumulative_volume_liters: float
    operating_hours: float
    previous_installation_id: Optional[UUID] = None
    removal_date: Optional[datetime] = None
    replacement_reason: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ===== Compatibility Check Schemas =====


class CompatibilityCheckRequest(BaseModel):
    purifier_model: str
    filter_id: UUID
    stage_position: Optional[int] = Field(None, ge=1)


class CompatibilityCheckResponse(BaseModel):
    result: CompatibilityResult
    reasons: List[str]
    details: Optional[Dict[str, Any]] = None


# ===== Maintenance Event Schemas =====


class MaintenanceEventBase(BaseModel):
    device_id: UUID
    event_type: MaintenanceEventType
    description: str
    initiated_by: Optional[str] = None
    filter_instance_id: Optional[UUID] = None
    evidence: Dict[str, Any] = Field(default_factory=dict)


class MaintenanceEventCreate(MaintenanceEventBase):
    pass


class MaintenanceEventResponse(MaintenanceEventBase):
    id: UUID
    timestamp: datetime
    pre_maintenance_state: Dict[str, Any]
    post_maintenance_state: Dict[str, Any]
    verification_status: Optional[str] = None
    correlation_id: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ===== Maintenance Workflow Schemas =====


class MaintenanceWorkflowTransition(BaseModel):
    new_state: str
    error_message: Optional[str] = None


class MaintenanceWorkflowResponse(BaseModel):
    id: UUID
    device_id: UUID
    maintenance_event_id: UUID
    state: MaintenanceWorkflowState
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    failed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ===== Calibration Schemas =====


class CalibrationRecordBase(BaseModel):
    device_id: UUID
    sensor_id: str
    sensor_type: str
    calibration_method: str
    reference_standard: str
    reference_value: float
    measured_value: float
    tolerance: float
    technician: Optional[str] = None
    notes: Optional[str] = None


class CalibrationRecordCreate(CalibrationRecordBase):
    pass


class CalibrationRecordResponse(CalibrationRecordBase):
    id: UUID
    calibration_date: datetime
    correction_offset: float
    result: str
    next_calibration_due: Optional[datetime] = None
    calibration_state: CalibrationState
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CalibrationDueResponse(BaseModel):
    sensor_type: str
    sensor_id: str
    status: str
    last_calibration: Optional[datetime] = None
    next_due: Optional[datetime] = None
    days_overdue: Optional[int] = None
    message: Optional[str] = None


# ===== Verification Schemas =====


class VerificationRunStart(BaseModel):
    device_id: UUID
    maintenance_event_id: UUID
    baseline_before: Optional[Dict[str, Any]] = None


class VerificationRunComplete(BaseModel):
    current_readings: Dict[str, float]


class VerificationRunResponse(BaseModel):
    id: UUID
    maintenance_event_id: UUID
    device_id: UUID
    state: VerificationState
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    checks: List[Dict[str, Any]] = Field(default_factory=list)
    overall_result: Optional[bool] = None
    failure_reasons: List[str] = Field(default_factory=list)
    baseline_before: Optional[Dict[str, Any]] = None
    baseline_after: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ===== Baseline Version Schemas =====


class BaselineVersionResponse(BaseModel):
    id: UUID
    device_id: UUID
    version: int
    maintenance_event_id: Optional[UUID] = None
    is_active: bool
    metrics: Dict[str, Any]
    created_at: datetime
    activated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ===== Maintenance Recommendation Schemas =====


class MaintenanceRecommendationResponse(BaseModel):
    id: UUID
    device_id: UUID
    filter_instance_id: Optional[UUID] = None
    trigger: str
    severity: str
    evidence: Dict[str, Any]
    urgency_days: Optional[int] = None
    recommended_action: str
    acknowledged_at: Optional[datetime] = None
    dismissed_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True
