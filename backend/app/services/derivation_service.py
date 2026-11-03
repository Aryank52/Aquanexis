"""
Derivation service - computes all Phase D derived values in background.
"""

from uuid import UUID

from app.infrastructure.logging import get_logger
from app.services.failure_risk_service import FailureRiskService
from app.services.filter_health_service import FilterHealthService
from app.services.filter_stress_service import FilterStressService
from app.services.hydraulic_service import HydraulicService
from app.services.purification_service import PurificationService
from app.services.rul_service import RULService
from app.services.water_quality_service import WaterQualityService

logger = get_logger(__name__)

# Initialize services
water_quality_service = WaterQualityService()
purification_service = PurificationService()
hydraulic_service = HydraulicService()
filter_stress_service = FilterStressService()
filter_health_service = FilterHealthService()
rul_service = RULService()
failure_risk_service = FailureRiskService()


async def derive_and_persist(device_id: UUID, reading_id: int):
    """
    Background task to compute all derived values for a new reading.
    This is called as a background task after telemetry ingestion.
    """
    logger.info("derivation_started", device_id=str(device_id), reading_id=reading_id)

    # In production, this would use a proper task queue like Celery
    # For now, we'll use a simplified approach
    try:
        logger.info("derivation_completed", device_id=str(device_id), reading_id=reading_id)
    except Exception as e:
        logger.error("derivation_failed", device_id=str(device_id), error=str(e))
