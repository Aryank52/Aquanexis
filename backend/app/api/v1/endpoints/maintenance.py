"""
Maintenance API endpoints.
"""
from datetime import datetime
from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database import get_db
from app.infrastructure.security import get_device_claims, verify_api_key
from app.infrastructure.logging import get_logger
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
    FilterLifecycleState,
    MaintenanceEventType,
    MaintenanceWorkflowState,
    VerificationState,
    CalibrationState,
)
from app.models.device import Device as DeviceModel
from app.schemas.maintenance import (
    FilterCatalogResponse,
    FilterCatalogCreate,
    FilterCatalogUpdate,
    InstalledFilterResponse,
    InstalledFilterInstall,
    InstalledFilterReplace,
    MaintenanceEventResponse,
    MaintenanceEventCreate,
    MaintenanceWorkflowResponse,
    MaintenanceWorkflowTransition,
    CalibrationRecordResponse,
    CalibrationRecordCreate,
    CalibrationDueResponse,
    VerificationRunResponse,
    VerificationRunStart,
    VerificationRunComplete,
    BaselineVersionResponse,
    MaintenanceRecommendationResponse,
    CompatibilityCheckRequest,
    CompatibilityCheckResponse,
)
from app.services.maintenance_service import MaintenanceService
from app.services.compatibility_engine import CompatibilityEngine

logger = get_logger(__name__)

router = APIRouter(prefix="/maintenance", tags=["maintenance"])


# ===== Filter Catalog =====

@router.get("/filters", response_model=List[FilterCatalogResponse])
async def list_filters(
    category: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    _: bool = Depends(verify_api_key),
):
    """List filter catalog entries."""
    service = MaintenanceService(db)
    
    category_enum = None
    if category:
        try:
            from app.domain.maintenance import FilterCategory
            category_enum = FilterCategory(category)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid category: {category}")
    
    filters = await service.list_filter_catalog(
        category=category_enum,
        is_active=is_active,
        limit=limit,
        offset=offset,
    )
    
    return [FilterCatalogResponse.model_validate(f) for f in filters]


@router.get("/filters/{filter_id}", response_model=FilterCatalogResponse)
async def get_filter(
    filter_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: bool = Depends(verify_api_key),
):
    """Get a filter catalog entry by ID."""
    service = MaintenanceService(db)
    catalog = await service.get_filter_catalog(filter_id)
    
    if not catalog:
        raise HTTPException(status_code=404, detail="Filter not found")
    
    return FilterCatalogResponse.model_validate(catalog)


@router.post("/filters", response_model=FilterCatalogResponse, status_code=status.HTTP_201_CREATED)
async def create_filter(
    filter_data: FilterCatalogCreate,
    db: AsyncSession = Depends(get_db),
    _: bool = Depends(verify_api_key),
):
    """Create a new filter catalog entry (admin only)."""
    service = MaintenanceService(db)
    
    from app.domain.maintenance import FilterCategory
    category_enum = FilterCategory(filter_data.category)
    
    catalog = await service.create_filter_catalog(
        filter_identifier=filter_data.filter_identifier,
        manufacturer=filter_data.manufacturer,
        product_name=filter_data.product_name,
        category=category_enum,
        purifier_compatibility=filter_data.purifier_compatibility,
        stage_position=filter_data.stage_position,
        specifications=filter_data.specifications,
        connector_details=filter_data.connector_details,
        dimensions_mm=filter_data.dimensions_mm,
        rated_service_interval_days=filter_data.rated_service_interval_days,
        rated_usage_volume_liters=filter_data.rated_usage_volume_liters,
        installation_requirements=filter_data.installation_requirements,
        maintenance_instructions=filter_data.maintenance_instructions,
        datasheet_reference=filter_data.datasheet_reference,
    )
    
    return FilterCatalogResponse.model_validate(catalog)


@router.patch("/filters/{filter_id}", response_model=FilterCatalogResponse)
async def update_filter(
    filter_id: UUID,
    filter_update: FilterCatalogUpdate,
    db: AsyncSession = Depends(get_db),
    _: bool = Depends(verify_api_key),
):
    """Update a filter catalog entry (admin only)."""
    catalog = await db.get(FilterCatalogModel, filter_id)
    if not catalog:
        raise HTTPException(status_code=404, detail="Filter not found")
    
    update_data = filter_update.model_dump(exclude_unset=True)
    
    if "category" in update_data:
        from app.domain.maintenance import FilterCategory
        update_data["category"] = FilterCategory(update_data["category"])
    
    for field, value in update_data.items():
        setattr(catalog, field, value)
    
    catalog.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(catalog)
    
    return FilterCatalogResponse.model_validate(catalog)


# ===== Installed Filters =====

@router.get("/devices/{device_id}/filters", response_model=List[InstalledFilterResponse])
async def list_installed_filters(
    device_id: UUID,
    db: AsyncSession = Depends(get_db),
    device_claims = Depends(get_device_claims),
):
    """List installed filters for a device."""
    if device_claims and device_claims.device_id != device_id:
        raise HTTPException(status_code=403, detail="Not authorized for this device")
    
    service = MaintenanceService(db)
    filters = await service.get_installed_filters(device_id)
    
    return [InstalledFilterResponse.model_validate(f) for f in filters]


@router.get("/devices/{device_id}/filters/{stage_position}", response_model=InstalledFilterResponse)
async def get_installed_filter(
    device_id: UUID,
    stage_position: int,
    db: AsyncSession = Depends(get_db),
    device_claims = Depends(get_device_claims),
):
    """Get active filter at a specific stage."""
    if device_claims and device_claims.device_id != device_id:
        raise HTTPException(status_code=403, detail="Not authorized for this device")
    
    service = MaintenanceService(db)
    filter_inst = await service.get_active_filter_at_stage(device_id, stage_position)
    
    if not filter_inst:
        raise HTTPException(status_code=404, detail="No active filter at this stage")
    
    return InstalledFilterResponse.model_validate(filter_inst)


@router.post("/devices/{device_id}/filters/install", response_model=InstalledFilterResponse)
async def install_filter(
    device_id: UUID,
    install_data: InstalledFilterInstall,
    db: AsyncSession = Depends(get_db),
    device_claims = Depends(get_device_claims),
):
    """Install a new filter on a device."""
    if device_claims and device_claims.device_id != device_id:
        raise HTTPException(status_code=403, detail="Not authorized for this device")
    
    service = MaintenanceService(db)
    
    try:
        installed = await service.install_filter(
            device_id=device_id,
            catalog_id=install_data.catalog_id,
            stage_position=install_data.stage_position,
            installer=install_data.installer,
            serial_number=install_data.serial_number,
            batch_identifier=install_data.batch_identifier,
        )
        return InstalledFilterResponse.model_validate(installed)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/devices/{device_id}/filters/replace", response_model=InstalledFilterResponse)
async def replace_filter(
    device_id: UUID,
    replace_data: InstalledFilterReplace,
    db: AsyncSession = Depends(get_db),
    device_claims = Depends(get_device_claims),
):
    """Replace a filter on a device."""
    if device_claims and device_claims.device_id != device_id:
        raise HTTPException(status_code=403, detail="Not authorized for this device")
    
    service = MaintenanceService(db)
    
    try:
        replaced = await service.replace_filter(
            device_id=device_id,
            stage_position=replace_data.stage_position,
            new_catalog_id=replace_data.new_catalog_id,
            installer=replace_data.installer,
            serial_number=replace_data.serial_number,
            batch_identifier=replace_data.batch_identifier,
            replacement_reason=replace_data.replacement_reason,
        )
        return InstalledFilterResponse.model_validate(replaced)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/filters/instances/{instance_id}", response_model=InstalledFilterResponse)
async def get_filter_instance(
    instance_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: bool = Depends(verify_api_key),
):
    """Get a filter instance by ID."""
    instance = await db.get(InstalledFilterModel, instance_id)
    if not instance:
        raise HTTPException(status_code=404, detail="Filter instance not found")
    
    return InstalledFilterResponse.model_validate(instance)


# ===== Compatibility Check =====

@router.post("/filters/compatibility/check", response_model=CompatibilityCheckResponse)
async def check_compatibility(
    request: CompatibilityCheckRequest,
    db: AsyncSession = Depends(get_db),
    _: bool = Depends(verify_api_key),
):
    """Check filter compatibility with a purifier model."""
    # Get filter catalog
    catalog = await db.get(FilterCatalogModel, request.filter_id)
    if not catalog:
        raise HTTPException(status_code=404, detail="Filter not found")
    
    from app.domain.maintenance import FilterCategory, FilterCatalog
    from app.services.compatibility_engine import CompatibilityEngine
    
    # Convert model to domain
    domain_catalog = FilterCatalog(
        id=catalog.id,
        filter_identifier=catalog.filter_identifier,
        manufacturer=catalog.manufacturer,
        product_name=catalog.product_name,
        category=FilterCategory(catalog.category.value),
        purifier_compatibility=catalog.purifier_compatibility,
        stage_position=catalog.stage_position,
        specifications=catalog.specifications,
        connector_details=catalog.connector_details,
        dimensions_mm=catalog.dimensions_mm,
        rated_service_interval_days=catalog.rated_service_interval_days,
        rated_usage_volume_liters=catalog.rated_usage_volume_liters,
        installation_requirements=catalog.installation_requirements,
        maintenance_instructions=catalog.maintenance_instructions,
        datasheet_reference=catalog.datasheet_reference,
        is_active=catalog.is_active,
        created_at=catalog.created_at,
        updated_at=catalog.updated_at,
    )
    
    engine = CompatibilityEngine()
    result = engine.check_compatibility(
        purifier_model=request.purifier_model,
        filter_catalog=domain_catalog,
        stage_position=request.stage_position,
    )
    
    return CompatibilityCheckResponse(
        result=result.result,
        reasons=result.reasons,
        details=result.details,
    )


# ===== Maintenance Events =====

@router.get("/events", response_model=List[MaintenanceEventResponse])
async def list_maintenance_events(
    device_id: Optional[UUID] = Query(None),
    event_type: Optional[str] = Query(None),
    start: Optional[datetime] = Query(None),
    end: Optional[datetime] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    device_claims = Depends(get_device_claims),
):
    """List maintenance events."""
    if device_id and device_claims and device_claims.device_id != device_id:
        raise HTTPException(status_code=403, detail="Not authorized for this device")
    
    if not device_id and device_claims:
        device_id = device_claims.device_id
    
    if not device_id:
        raise HTTPException(status_code=400, detail="Device ID required")
    
    service = MaintenanceService(db)
    
    event_type_enum = None
    if event_type:
        try:
            from app.domain.maintenance import MaintenanceEventType
            event_type_enum = MaintenanceEventType(event_type)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid event type: {event_type}")
    
    events = await service.get_maintenance_events(
        device_id=device_id,
        event_type=event_type_enum,
        limit=limit,
        offset=offset,
    )
    
    return [MaintenanceEventResponse.model_validate(e) for e in events]


@router.post("/events", response_model=MaintenanceEventResponse, status_code=status.HTTP_201_CREATED)
async def create_maintenance_event(
    event_data: MaintenanceEventCreate,
    db: AsyncSession = Depends(get_db),
    device_claims = Depends(get_device_claims),
):
    """Create a maintenance event."""
    if device_claims and device_claims.device_id != event_data.device_id:
        raise HTTPException(status_code=403, detail="Not authorized for this device")
    
    service = MaintenanceService(db)
    
    from app.domain.maintenance import MaintenanceEventType
    event_type_enum = MaintenanceEventType(event_data.event_type)
    
    event = await service.create_maintenance_event(
        device_id=event_data.device_id,
        event_type=event_type_enum,
        description=event_data.description,
        initiated_by=event_data.initiated_by,
        filter_instance_id=event_data.filter_instance_id,
        evidence=event_data.evidence,
    )
    
    return MaintenanceEventResponse.model_validate(event)


# ===== Maintenance Workflows =====

@router.get("/workflows/{workflow_id}", response_model=MaintenanceWorkflowResponse)
async def get_workflow(
    workflow_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: bool = Depends(verify_api_key),
):
    """Get a maintenance workflow."""
    workflow = await db.get(MaintenanceWorkflowModel, workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    return MaintenanceWorkflowResponse.model_validate(workflow)


@router.post("/workflows/{workflow_id}/transition", response_model=MaintenanceWorkflowResponse)
async def transition_workflow(
    workflow_id: UUID,
    transition: MaintenanceWorkflowTransition,
    db: AsyncSession = Depends(get_db),
    _: bool = Depends(verify_api_key),
):
    """Transition a maintenance workflow state."""
    service = MaintenanceService(db)
    
    from app.domain.maintenance import MaintenanceWorkflowState
    try:
        new_state = MaintenanceWorkflowState(transition.new_state)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid state: {transition.new_state}")
    
    try:
        workflow = await service.transition_workflow(
            workflow_id=workflow_id,
            new_state=new_state,
            error_message=transition.error_message,
        )
        return MaintenanceWorkflowResponse.model_validate(workflow)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ===== Calibration =====

@router.get("/calibration/due", response_model=List[CalibrationDueResponse])
async def get_calibration_due(
    device_id: UUID,
    db: AsyncSession = Depends(get_db),
    device_claims = Depends(get_device_claims),
):
    """Get sensors due for calibration."""
    if device_claims and device_claims.device_id != device_id:
        raise HTTPException(status_code=403, detail="Not authorized for this device")
    
    service = MaintenanceService(db)
    due = await service.get_calibration_due(device_id)
    
    return [CalibrationDueResponse(**d) for d in due]


@router.get("/calibration", response_model=List[CalibrationRecordResponse])
async def list_calibration_records(
    device_id: UUID,
    sensor_type: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    device_claims = Depends(get_device_claims),
):
    """List calibration records for a device."""
    if device_claims and device_claims.device_id != device_id:
        raise HTTPException(status_code=403, detail="Not authorized for this device")
    
    service = MaintenanceService(db)
    records = await service.get_calibration_records(device_id, sensor_type, limit)
    
    return [CalibrationRecordResponse.model_validate(r) for r in records]


@router.post("/calibration", response_model=CalibrationRecordResponse, status_code=status.HTTP_201_CREATED)
async def record_calibration(
    cal_data: CalibrationRecordCreate,
    db: AsyncSession = Depends(get_db),
    device_claims = Depends(get_device_claims),
):
    """Record a calibration event."""
    if device_claims and device_claims.device_id != cal_data.device_id:
        raise HTTPException(status_code=403, detail="Not authorized for this device")
    
    service = MaintenanceService(db)
    
    calibration = await service.record_calibration(
        device_id=cal_data.device_id,
        sensor_id=cal_data.sensor_id,
        sensor_type=cal_data.sensor_type,
        calibration_method=cal_data.calibration_method,
        reference_standard=cal_data.reference_standard,
        reference_value=cal_data.reference_value,
        measured_value=cal_data.measured_value,
        tolerance=cal_data.tolerance,
        technician=cal_data.technician,
        notes=cal_data.notes,
    )
    
    return CalibrationRecordResponse.model_validate(calibration)


# ===== Verification =====

@router.post("/verification/start", response_model=VerificationRunResponse)
async def start_verification(
    request: VerificationRunStart,
    db: AsyncSession = Depends(get_db),
    device_claims = Depends(get_device_claims),
):
    """Start a post-maintenance verification run."""
    if device_claims and device_claims.device_id != request.device_id:
        raise HTTPException(status_code=403, detail="Not authorized for this device")
    
    service = MaintenanceService(db)
    
    verification = await service.start_verification(
        maintenance_event_id=request.maintenance_event_id,
        baseline_before=request.baseline_before,
    )
    
    return VerificationRunResponse.model_validate(verification)


@router.post("/verification/{verification_id}/complete", response_model=VerificationRunResponse)
async def complete_verification(
    verification_id: UUID,
    request: VerificationRunComplete,
    db: AsyncSession = Depends(get_db),
    device_claims = Depends(get_device_claims),
):
    """Complete a verification run with current readings."""
    verification = await db.get(VerificationRunModel, verification_id)
    if not verification:
        raise HTTPException(status_code=404, detail="Verification not found")
    
    if device_claims and device_claims.device_id != verification.device_id:
        raise HTTPException(status_code=403, detail="Not authorized for this device")
    
    service = MaintenanceService(db)
    
    verification = await service.run_verification_checks(
        verification_id=verification_id,
        current_readings=request.current_readings,
    )
    
    # If passed, create new baseline version
    if verification.overall_result:
        maintenance_event = await db.get(MaintenanceEventModel, verification.maintenance_event_id)
        if maintenance_event:
            service = MaintenanceService(db)
            await service.create_baseline_version(
                device_id=verification.device_id,
                maintenance_event_id=verification.maintenance_event_id,
                metrics=request.current_readings,
            )
    
    return VerificationRunResponse.model_validate(verification)


@router.get("/verification/{verification_id}", response_model=VerificationRunResponse)
async def get_verification(
    verification_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: bool = Depends(verify_api_key),
):
    """Get a verification run."""
    verification = await db.get(VerificationRunModel, verification_id)
    if not verification:
        raise HTTPException(status_code=404, detail="Verification not found")
    
    return VerificationRunResponse.model_validate(verification)


# ===== Baseline Versions =====

@router.get("/baseline/{device_id}", response_model=BaselineVersionResponse)
async def get_active_baseline(
    device_id: UUID,
    db: AsyncSession = Depends(get_db),
    device_claims = Depends(get_device_claims),
):
    """Get the active baseline for a device."""
    if device_claims and device_claims.device_id != device_id:
        raise HTTPException(status_code=403, detail="Not authorized for this device")
    
    service = MaintenanceService(db)
    baseline = await service.get_active_baseline(device_id)
    
    if not baseline:
        raise HTTPException(status_code=404, detail="No active baseline found")
    
    return BaselineVersionResponse.model_validate(baseline)


# ===== Maintenance Recommendations =====

@router.get("/recommendations", response_model=List[MaintenanceRecommendationResponse])
async def get_recommendations(
    device_id: UUID,
    db: AsyncSession = Depends(get_db),
    device_claims = Depends(get_device_claims),
):
    """Get maintenance recommendations for a device."""
    if device_claims and device_claims.device_id != device_id:
        raise HTTPException(status_code=403, detail="Not authorized for this device")
    
    service = MaintenanceService(db)
    recommendations = await service.generate_recommendations(device_id)
    
    return [MaintenanceRecommendationResponse.model_validate(r) for r in recommendations]


# Need to import datetime
from datetime import datetime