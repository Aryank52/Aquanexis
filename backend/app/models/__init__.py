"""
Database models package.
Import all models here so they're registered with SQLAlchemy Base.
"""
from app.models.device import Device
from app.models.reading import SensorReading
from app.models.alert import Alert
from app.models.water_quality import WaterQualityScore
from app.models.filter_health import FilterHealth
from app.models.purification_performance import PurificationPerformance
from app.models.system_diagnostics import SystemDiagnostics
from app.models.safety import SafetyEventModel, SafetyActionModel
from app.models.notification import (
    NotificationOutbox,
    NotificationProviderConfig,
    NotificationTemplate,
    NotificationChannel,
    NotificationStatus,
    NotificationErrorCategory,
)
from app.models.maintenance import (
    FilterCatalogModel,
    InstalledFilterModel,
    MaintenanceEventModel,
    MaintenanceWorkflowModel,
    CalibrationRecordModel,
    CalibrationPolicyModel,
    VerificationRunModel,
    BaselineVersionModel,
    MaintenanceRecommendationModel,
    FilterCategory,
    FilterLifecycleState,
    MaintenanceEventType,
    MaintenanceWorkflowState,
    CalibrationState,
    VerificationState,
)

__all__ = [
    "Device", 
    "SensorReading", 
    "Alert",
    "WaterQualityScore",
    "FilterHealth",
    "PurificationPerformance",
    "SystemDiagnostics",
    "SafetyEventModel",
    "SafetyActionModel",
    "NotificationOutbox",
    "NotificationProviderConfig",
    "NotificationTemplate",
    "NotificationChannel",
    "NotificationStatus",
    "NotificationErrorCategory",
    "FilterCatalogModel",
    "InstalledFilterModel",
    "MaintenanceEventModel",
    "MaintenanceWorkflowModel",
    "CalibrationRecordModel",
    "CalibrationPolicyModel",
    "VerificationRunModel",
    "BaselineVersionModel",
    "MaintenanceRecommendationModel",
    "FilterCategory",
    "FilterLifecycleState",
    "MaintenanceEventType",
    "MaintenanceWorkflowState",
    "CalibrationState",
    "VerificationState",
]