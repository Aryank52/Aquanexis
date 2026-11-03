"""
Database models package.
Import all models here so they're registered with SQLAlchemy Base.
"""

from app.models.alert import Alert
from app.models.device import Device
from app.models.filter_health import FilterHealth
from app.models.maintenance import (
    BaselineVersionModel,
    CalibrationPolicyModel,
    CalibrationRecordModel,
    CalibrationState,
    FilterCatalogModel,
    FilterCategory,
    FilterLifecycleState,
    InstalledFilterModel,
    MaintenanceEventModel,
    MaintenanceEventType,
    MaintenanceRecommendationModel,
    MaintenanceWorkflowModel,
    MaintenanceWorkflowState,
    VerificationRunModel,
    VerificationState,
)
from app.models.notification import (
    NotificationChannel,
    NotificationErrorCategory,
    NotificationOutbox,
    NotificationProviderConfig,
    NotificationStatus,
    NotificationTemplate,
)
from app.models.purification_performance import PurificationPerformance
from app.models.reading import SensorReading
from app.models.safety import SafetyActionModel, SafetyEventModel
from app.models.system_diagnostics import SystemDiagnostics
from app.models.water_quality import WaterQualityScore

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
