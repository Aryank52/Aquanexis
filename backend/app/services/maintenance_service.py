"""
Maintenance Service - handles filter installation, replacement, and maintenance workflows.
"""
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4

from sqlalchemy import select, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession

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
)
from app.models.device import Device as DeviceModel
from app.models.alert import Alert as AlertModel, AlertSeverity, AlertStatus
from app.domain.maintenance import (
    FilterCatalog,
    InstalledFilter,
    MaintenanceEvent,
    MaintenanceWorkflow,
    CalibrationRecord,
    CalibrationPolicy,
    VerificationRun,
    VerificationCheck,
    VerificationState as DomainVerificationState,
    BaselineVersion,
    MaintenanceRecommendation,
    FilterCategory,
    MaintenanceEventType,
    MaintenanceWorkflowState,
    DEFAULT_CALIBRATION_POLICIES,
)
from app.services.notification_service import NotificationService

logger = get_logger(__name__)


class MaintenanceService:
    """Service for managing maintenance operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.notification_service = NotificationService(db)
    
    # ===== Filter Catalog =====
    
    async def create_filter_catalog(
        self,
        filter_identifier: str,
        manufacturer: str,
        product_name: str,
        category: FilterCategory,
        purifier_compatibility: List[str],
        stage_position: int,
        specifications: Dict[str, Any] = None,
        connector_details: Optional[str] = None,
        dimensions_mm: Optional[Dict[str, float]] = None,
        rated_service_interval_days: Optional[int] = None,
        rated_usage_volume_liters: Optional[float] = None,
        installation_requirements: Optional[str] = None,
        maintenance_instructions: Optional[str] = None,
        datasheet_reference: Optional[str] = None,
    ) -> FilterCatalogModel:
        """Create a new filter catalog entry."""
        catalog = FilterCatalogModel(
            filter_identifier=filter_identifier,
            manufacturer=manufacturer,
            product_name=product_name,
            category=category,
            purifier_compatibility=purifier_compatibility,
            stage_position=stage_position,
            specifications=specifications or {},
            connector_details=connector_details,
            dimensions_mm=dimensions_mm,
            rated_service_interval_days=rated_service_interval_days,
            rated_usage_volume_liters=rated_usage_volume_liters,
            installation_requirements=installation_requirements,
            maintenance_instructions=maintenance_instructions,
            datasheet_reference=datasheet_reference,
        )
        
        self.db.add(catalog)
        await self.db.commit()
        await self.db.refresh(catalog)
        
        logger.info("filter_catalog_created", catalog_id=str(catalog.id), identifier=filter_identifier)
        return catalog
    
    async def get_filter_catalog(self, catalog_id: UUID) -> Optional[FilterCatalogModel]:
        """Get filter catalog by ID."""
        return await self.db.get(FilterCatalogModel, catalog_id)
    
    async def list_filter_catalog(
        self,
        category: Optional[FilterCategory] = None,
        is_active: Optional[bool] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[FilterCatalogModel]:
        """List filter catalog entries with filtering."""
        query = select(FilterCatalogModel)
        
        if category:
            query = query.where(FilterCatalogModel.category == category)
        if is_active is not None:
            query = query.where(FilterCatalogModel.is_active == is_active)
        
        query = query.order_by(FilterCatalogModel.created_at.desc()).limit(limit).offset(offset)
        result = await self.db.execute(query)
        return result.scalars().all()
    
    # ===== Installed Filters =====
    
    async def install_filter(
        self,
        device_id: UUID,
        catalog_id: UUID,
        stage_position: int,
        installer: Optional[str] = None,
        serial_number: Optional[str] = None,
        batch_identifier: Optional[str] = None,
    ) -> InstalledFilterModel:
        """Install a new filter on a device."""
        # Verify device exists
        device = await self.db.get(DeviceModel, device_id)
        if not device:
            raise ValueError(f"Device {device_id} not found")
        
        # Verify catalog exists
        catalog = await self.db.get(FilterCatalogModel, catalog_id)
        if not catalog:
            raise ValueError(f"Filter catalog {catalog_id} not found")
        
        # Check for existing active filter at same stage
        existing = await self.db.execute(
            select(InstalledFilterModel).where(
                and_(
                    InstalledFilterModel.device_id == device_id,
                    InstalledFilterModel.stage_position == stage_position,
                    InstalledFilterModel.lifecycle_state == FilterLifecycleState.INSTALLED,
                )
            )
        )
        if existing.scalar_one_or_none():
            raise ValueError(f"Device {device_id} already has an active filter at stage {stage_position}")
        
        # Create installed filter
        installed = InstalledFilterModel(
            device_id=device_id,
            catalog_id=catalog_id,
            stage_position=stage_position,
            installer=installer,
            serial_number=serial_number,
            batch_identifier=batch_identifier,
            lifecycle_state=FilterLifecycleState.INSTALLED,
        )
        
        self.db.add(installed)
        await self.db.commit()
        await self.db.refresh(installed)
        
        # Create maintenance event
        await self._create_maintenance_event(
            device_id=device_id,
            filter_instance_id=installed.id,
            event_type=MaintenanceEventType.INSTALL,
            description=f"Installed filter {catalog.product_name} at stage {stage_position}",
            initiated_by=installer or "system",
        )
        
        # Create calibration policies for the new filter's sensors
        await self._create_default_calibration_policies(device_id)
        
        logger.info("filter_installed", device_id=str(device_id), filter_id=str(installed.id), catalog_id=str(catalog_id))
        return installed
    
    async def replace_filter(
        self,
        device_id: UUID,
        stage_position: int,
        new_catalog_id: UUID,
        installer: Optional[str] = None,
        serial_number: Optional[str] = None,
        batch_identifier: Optional[str] = None,
        replacement_reason: Optional[str] = None,
    ) -> InstalledFilterModel:
        """Replace an existing filter with a new one."""
        # Find current installed filter at this stage
        current = await self.db.execute(
            select(InstalledFilterModel).where(
                and_(
                    InstalledFilterModel.device_id == device_id,
                    InstalledFilterModel.stage_position == stage_position,
                    InstalledFilterModel.lifecycle_state == FilterLifecycleState.INSTALLED,
                )
            )
        )
        current_filter = current.scalar_one_or_none()
        
        if not current_filter:
            raise ValueError(f"No active filter found at stage {stage_position} on device {device_id}")
        
        # Verify new catalog exists
        new_catalog = await self.db.get(FilterCatalogModel, new_catalog_id)
        if not new_catalog:
            raise ValueError(f"Filter catalog {new_catalog_id} not found")
        
        # Mark old filter as removed
        current_filter.lifecycle_state = FilterLifecycleState.REMOVED
        current_filter.removal_date = datetime.utcnow()
        current_filter.replacement_reason = replacement_reason
        current_filter.updated_at = datetime.utcnow()
        
        # Create new installed filter
        new_installed = InstalledFilterModel(
            device_id=device_id,
            catalog_id=new_catalog_id,
            stage_position=stage_position,
            installer=installer,
            serial_number=serial_number,
            batch_identifier=batch_identifier,
            lifecycle_state=FilterLifecycleState.INSTALLED,
            previous_installation_id=current_filter.id,
        )
        
        self.db.add(new_installed)
        await self.db.commit()
        await self.db.refresh(new_installed)
        
        # Create maintenance event for replacement
        await self._create_maintenance_event(
            device_id=device_id,
            filter_instance_id=new_installed.id,
            event_type=MaintenanceEventType.REPLACE,
            description=f"Replaced filter {current_filter.catalog.product_name if current_filter.catalog else 'unknown'} with {new_catalog.product_name}",
            initiated_by=installer or "system",
            evidence={
                "old_filter_id": str(current_filter.id),
                "old_catalog_id": str(current_filter.catalog_id),
                "new_filter_id": str(new_installed.id),
                "new_catalog_id": str(new_catalog_id),
                "replacement_reason": replacement_reason,
            },
        )
        
        # Create maintenance workflow for replacement
        await self._create_maintenance_workflow(
            device_id=device_id,
            maintenance_event_id=new_installed.id,
            state=MaintenanceWorkflowState.IN_PROGRESS,
        )
        
        logger.info("filter_replaced", device_id=str(device_id), old_filter_id=str(current_filter.id), new_filter_id=str(new_installed.id))
        return new_installed
    
    async def get_installed_filters(self, device_id: UUID) -> List[InstalledFilterModel]:
        """Get all installed filters for a device."""
        result = await self.db.execute(
            select(InstalledFilterModel).where(InstalledFilterModel.device_id == device_id)
        )
        return result.scalars().all()
    
    async def get_active_filter_at_stage(self, device_id: UUID, stage_position: int) -> Optional[InstalledFilterModel]:
        """Get active filter at a specific stage."""
        result = await self.db.execute(
            select(InstalledFilterModel).where(
                and_(
                    InstalledFilterModel.device_id == device_id,
                    InstalledFilterModel.stage_position == stage_position,
                    InstalledFilterModel.lifecycle_state == FilterLifecycleState.INSTALLED,
                )
            )
        )
        return result.scalar_one_or_none()
    
    # ===== Maintenance Events =====
    
    async def _create_maintenance_event(
        self,
        device_id: UUID,
        event_type: MaintenanceEventType,
        description: str,
        initiated_by: Optional[str] = None,
        filter_instance_id: Optional[UUID] = None,
        evidence: Optional[Dict[str, Any]] = None,
    ) -> MaintenanceEventModel:
        """Create a maintenance event record."""
        event = MaintenanceEventModel(
            device_id=device_id,
            filter_instance_id=filter_instance_id,
            event_type=event_type,
            description=description,
            initiated_by=initiated_by,
            evidence=evidence or {},
        )
        
        self.db.add(event)
        await self.db.commit()
        await self.db.refresh(event)
        
        # Enqueue notification
        await self._enqueue_maintenance_notification(
            device_id=device_id,
            event_type=event_type,
            message=description,
        )
        
        return event
    
    async def create_maintenance_event(
        self,
        device_id: UUID,
        event_type: MaintenanceEventType,
        description: str,
        initiated_by: Optional[str] = None,
        filter_instance_id: Optional[UUID] = None,
        evidence: Optional[Dict[str, Any]] = None,
    ) -> MaintenanceEventModel:
        """Public method to create a maintenance event."""
        return await self._create_maintenance_event(
            device_id=device_id,
            event_type=event_type,
            description=description,
            initiated_by=initiated_by,
            filter_instance_id=filter_instance_id,
            evidence=evidence,
        )
    
    async def get_maintenance_events(
        self,
        device_id: UUID,
        event_type: Optional[MaintenanceEventType] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[MaintenanceEventModel]:
        """Get maintenance events for a device."""
        query = select(MaintenanceEventModel).where(MaintenanceEventModel.device_id == device_id)
        
        if event_type:
            query = query.where(MaintenanceEventModel.event_type == event_type)
        
        query = query.order_by(MaintenanceEventModel.timestamp.desc()).limit(limit).offset(offset)
        result = await self.db.execute(query)
        return result.scalars().all()
    
    # ===== Maintenance Workflow =====
    
    async def _create_maintenance_workflow(
        self,
        device_id: UUID,
        maintenance_event_id: UUID,
        state: MaintenanceWorkflowState = MaintenanceWorkflowState.REQUESTED,
    ) -> MaintenanceWorkflowModel:
        """Create a maintenance workflow."""
        workflow = MaintenanceWorkflowModel(
            device_id=device_id,
            maintenance_event_id=maintenance_event_id,
            state=state,
        )
        
        self.db.add(workflow)
        await self.db.commit()
        await self.db.refresh(workflow)
        return workflow
    
    async def transition_workflow(
        self,
        workflow_id: UUID,
        new_state: MaintenanceWorkflowState,
        error_message: Optional[str] = None,
    ) -> MaintenanceWorkflowModel:
        """Transition a maintenance workflow to a new state."""
        workflow = await self.db.get(MaintenanceWorkflowModel, workflow_id)
        if not workflow:
            raise ValueError(f"Workflow {workflow_id} not found")
        
        # Validate transition
        from app.domain.maintenance import MAINTENANCE_WORKFLOW_TRANSITIONS
        if new_state not in MAINTENANCE_WORKFLOW_TRANSITIONS.get(workflow.state, []):
            raise ValueError(f"Invalid transition from {workflow.state} to {new_state}")
        
        # Perform transition
        workflow.state = new_state
        now = datetime.utcnow()
        
        if new_state == MaintenanceWorkflowState.IN_PROGRESS:
            workflow.started_at = now
        elif new_state == MaintenanceWorkflowState.COMPLETED:
            workflow.completed_at = now
        elif new_state == MaintenanceWorkflowState.VERIFIED:
            workflow.completed_at = now
        elif new_state == MaintenanceWorkflowState.FAILED:
            workflow.failed_at = now
            workflow.error_message = error_message
        
        workflow.updated_at = now
        await self.db.commit()
        await self.db.refresh(workflow)
        
        return workflow
    
    # ===== Calibration Management =====
    
    async def _create_default_calibration_policies(self, device_id: UUID) -> None:
        """Create default calibration policies for a new device."""
        for sensor_type, policy in DEFAULT_CALIBRATION_POLICIES.items():
            # Create policy for each sensor type
            policy_obj = CalibrationPolicyModel(
                device_id=device_id,
                sensor_id=sensor_type,
                sensor_type=sensor_type,
                time_interval_days=policy.get("time_days"),
                usage_interval_measurements=policy.get("usage_measurements"),
            )
            self.db.add(policy_obj)
        
        await self.db.commit()
    
    async def record_calibration(
        self,
        device_id: UUID,
        sensor_id: str,
        sensor_type: str,
        calibration_method: str,
        reference_standard: str,
        reference_value: float,
        measured_value: float,
        tolerance: float,
        technician: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> CalibrationRecordModel:
        """Record a calibration event."""
        correction_offset = measured_value - reference_value
        result = "PASS" if abs(correction_offset) <= tolerance else "FAIL"
        
        # Calculate next due date
        policy = await self.db.execute(
            select(CalibrationPolicyModel).where(
                and_(
                    CalibrationPolicyModel.device_id == device_id,
                    CalibrationPolicyModel.sensor_type == sensor_type,
                    CalibrationPolicyModel.is_active == True,
                )
            )
        )
        policy_obj = policy.scalar_one_or_none()
        
        next_due = None
        if policy_obj and policy_obj.time_interval_days:
            next_due = datetime.utcnow() + timedelta(days=policy_obj.time_interval_days)
        
        calibration = CalibrationRecordModel(
            device_id=device_id,
            sensor_id=sensor_id,
            sensor_type=sensor_type,
            calibration_method=calibration_method,
            reference_standard=reference_standard,
            reference_value=reference_value,
            measured_value=measured_value,
            correction_offset=correction_offset,
            tolerance=tolerance,
            result=result,
            technician=technician,
            notes=notes,
            next_calibration_due=next_due,
            calibration_state="valid" if result == "PASS" else "failed",
        )
        
        self.db.add(calibration)
        await self.db.commit()
        await self.db.refresh(calibration)
        
        # Update policy with next due
        if policy_obj:
            policy_obj.updated_at = datetime.utcnow()
            await self.db.commit()
        
        # Enqueue notification if calibration failed
        if result == "FAIL":
            await self._enqueue_calibration_notification(device_id, sensor_type, "calibration_failed")
        
        logger.info("calibration_recorded", device_id=str(device_id), sensor_type=sensor_type, result=result)
        return calibration
    
    async def get_calibration_records(
        self,
        device_id: UUID,
        sensor_type: Optional[str] = None,
        limit: int = 50,
    ) -> List[CalibrationRecordModel]:
        """Get calibration records for a device."""
        query = select(CalibrationRecordModel).where(CalibrationRecordModel.device_id == device_id)
        
        if sensor_type:
            query = query.where(CalibrationRecordModel.sensor_type == sensor_type)
        
        query = query.order_by(CalibrationRecordModel.calibration_date.desc()).limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def get_calibration_due(self, device_id: UUID) -> List[Dict[str, Any]]:
        """Get sensors due for calibration."""
        # Get all active policies
        policies = await self.db.execute(
            select(CalibrationPolicyModel).where(
                and_(
                    CalibrationPolicyModel.device_id == device_id,
                    CalibrationPolicyModel.is_active == True,
                )
            )
        )
        policies_list = policies.scalars().all()
        
        due_sensors = []
        now = datetime.utcnow()
        
        for policy in policies_list:
            # Get latest calibration
            latest = await self.db.execute(
                select(CalibrationRecordModel).where(
                    and_(
                        CalibrationRecordModel.device_id == device_id,
                        CalibrationRecordModel.sensor_type == policy.sensor_type,
                    )
                ).order_by(CalibrationRecordModel.calibration_date.desc()).limit(1)
            )
            latest_cal = latest.scalar_one_or_none()
            
            if not latest_cal:
                # Never calibrated
                due_sensors.append({
                    "sensor_type": policy.sensor_type,
                    "sensor_id": policy.sensor_id,
                    "status": "overdue",
                    "message": "Never calibrated",
                    "days_overdue": None,
                })
                continue
            
            # Check time-based due
            time_due = False
            days_overdue = None
            if policy.time_interval_days and latest_cal.next_calibration_due:
                if latest_cal.next_calibration_due <= now:
                    time_due = True
                    days_overdue = (now - latest_cal.next_calibration_due).days
                elif (latest_cal.next_calibration_due - now).days <= 7:
                    time_due = True  # Due soon
            
            # Check usage-based due (simplified - would need actual usage tracking)
            usage_due = False
            
            if time_due or usage_due:
                due_sensors.append({
                    "sensor_type": policy.sensor_type,
                    "sensor_id": policy.sensor_id,
                    "status": "overdue" if time_due else "due_soon",
                    "last_calibration": latest_cal.calibration_date.isoformat(),
                    "next_due": latest_cal.next_calibration_due.isoformat() if latest_cal.next_calibration_due else None,
                    "days_overdue": days_overdue,
                })
        
        return due_sensors
    
    # ===== Post-Maintenance Verification =====
    
    async def start_verification(
        self,
        maintenance_event_id: UUID,
        baseline_before: Optional[Dict[str, Any]] = None,
    ) -> VerificationRunModel:
        """Start a post-maintenance verification run."""
        # Get maintenance event
        event = await self.db.get(MaintenanceEventModel, maintenance_event_id)
        if not event:
            raise ValueError(f"Maintenance event {maintenance_event_id} not found")
        
        # Create verification run
        verification = VerificationRunModel(
            maintenance_event_id=maintenance_event_id,
            device_id=event.device_id,
            state=VerificationState.RUNNING,
            started_at=datetime.utcnow(),
            baseline_before=baseline_before or {},
        )
        
        self.db.add(verification)
        await self.db.commit()
        await self.db.refresh(verification)
        
        # Update workflow state
        workflows = await self.db.execute(
            select(MaintenanceWorkflowModel).where(
                MaintenanceWorkflowModel.maintenance_event_id == maintenance_event_id
            )
        )
        workflow = workflows.scalar_one_or_none()
        if workflow:
            workflow.state = MaintenanceWorkflowState.AWAITING_VERIFICATION
            await self.db.commit()
        
        # Update maintenance event verification status
        event.verification_status = VerificationState.RUNNING.value
        await self.db.commit()
        
        logger.info("verification_started", maintenance_event_id=str(maintenance_event_id), verification_id=str(verification.id))
        return verification
    
    async def run_verification_checks(
        self,
        verification_id: UUID,
        current_readings: Dict[str, float],
    ) -> VerificationRunModel:
        """Run verification checks against current readings."""
        verification = await self.db.get(VerificationRunModel, verification_id)
        if not verification:
            raise ValueError(f"Verification {verification_id} not found")
        
        checks = []
        all_passed = True
        failure_reasons = []
        
        # Define verification checks based on maintenance type
        # This is simplified - in production would be more sophisticated
        baseline = verification.baseline_before or {}
        
        checks_config = [
            {
                "name": "flow_rate",
                "description": "Flow rate within acceptable range",
                "expected_range": {"min": 0.5, "max": 5.0},  # L/min
                "key": "flow_rate",
            },
            {
                "name": "inlet_pressure",
                "description": "Inlet pressure within acceptable range",
                "expected_range": {"min": 100, "max": 600},  # kPa
                "key": "inlet_pressure",
            },
            {
                "name": "outlet_pressure",
                "description": "Outlet pressure within acceptable range",
                "expected_range": {"min": 50, "max": 500},  # kPa
                "key": "outlet_pressure",
            },
            {
                "name": "tds",
                "description": "TDS within acceptable range",
                "expected_range": {"min": 0, "max": 500},  # ppm
                "key": "tds",
            },
            {
                "name": "leak_detected",
                "description": "No leak detected",
                "expected_range": {"min": 0, "max": 0},  # boolean as 0/1
                "key": "leak_detected",
            },
        ]
        
        for check_config in checks_config:
            key = check_config["key"]
            expected = check_config["expected_range"]
            actual = current_readings.get(key)
            
            if actual is None:
                check = VerificationCheck(
                    name=check_config["name"],
                    description=check_config["description"],
                    expected_range=expected,
                    actual_value=None,
                    passed=None,
                    check_type="unavailable",
                )
                failure_reasons.append(f"{check_config['name']}: sensor data unavailable")
                continue
            
            # Check if actual value is within expected range
            passed = expected["min"] <= actual <= expected["max"]
            
            check = VerificationCheck(
                name=check_config["name"],
                description=check_config["description"],
                expected_range=expected,
                actual_value=actual,
                passed=passed,
                check_type="measured",
            )
            
            if not passed:
                all_passed = False
                failure_reasons.append(f"{check_config['name']}: {actual} outside range {expected['min']}-{expected['max']}")
            
            checks.append(check)
        
        # Compare against baseline if available
        if baseline:
            for key, value in baseline.items():
                if key in current_readings:
                    baseline_value = value
                    current_value = current_readings[key]
                    # Check if within 20% of baseline
                    if baseline_value > 0:
                        deviation = abs(current_value - baseline_value) / baseline_value * 100
                        if deviation > 20:
                            all_passed = False
                            failure_reasons.append(f"{key}: {deviation:.1f}% deviation from baseline")
        
        # Update verification run
        verification.checks = [c.__dict__ for c in checks]
        verification.overall_result = all_passed
        verification.failure_reasons = failure_reasons
        verification.state = VerificationState.PASSED if all_passed else VerificationState.FAILED
        verification.completed_at = datetime.utcnow()
        verification.baseline_after = current_readings
        verification.updated_at = datetime.utcnow()
        
        await self.db.commit()
        await self.db.refresh(verification)
        
        # Update maintenance event
        event = await self.db.get(MaintenanceEventModel, verification.maintenance_event_id)
        if event:
            event.verification_status = verification.state.value
            await self.db.commit()
        
        # Update workflow
        workflows = await self.db.execute(
            select(MaintenanceWorkflowModel).where(
                MaintenanceWorkflowModel.maintenance_event_id == verification.maintenance_event_id
            )
        )
        workflow = workflows.scalar_one_or_none()
        if workflow:
            if all_passed:
                workflow.state = MaintenanceWorkflowState.VERIFIED
            else:
                workflow.state = MaintenanceWorkflowState.FAILED
                workflow.error_message = "; ".join(failure_reasons)
            workflow.completed_at = datetime.utcnow()
            await self.db.commit()
        
        # Enqueue notification
        await self._enqueue_verification_notification(
            device_id=verification.device_id,
            passed=all_passed,
            failure_reasons=failure_reasons,
        )
        
        logger.info("verification_completed", verification_id=str(verification_id), passed=all_passed)
        return verification
    
    # ===== Baseline Versioning =====
    
    async def create_baseline_version(
        self,
        device_id: UUID,
        maintenance_event_id: UUID,
        metrics: Dict[str, Any],
    ) -> BaselineVersionModel:
        """Create a new baseline version after successful maintenance."""
        # Get current active baseline version
        current = await self.db.execute(
            select(BaselineVersionModel).where(
                and_(
                    BaselineVersionModel.device_id == device_id,
                    BaselineVersionModel.is_active == True,
                )
            )
        )
        current_baseline = current.scalar_one_or_none()
        
        # Deactivate current baseline
        if current_baseline:
            current_baseline.is_active = False
        
        # Get next version number
        version_num = 1
        if current_baseline:
            version_num = current_baseline.version + 1
        
        # Create new baseline
        new_baseline = BaselineVersionModel(
            device_id=device_id,
            version=version_num,
            maintenance_event_id=maintenance_event_id,
            is_active=True,
            metrics=metrics,
            activated_at=datetime.utcnow(),
        )
        
        self.db.add(new_baseline)
        await self.db.commit()
        await self.db.refresh(new_baseline)
        
        logger.info("baseline_version_created", device_id=str(device_id), version=version_num)
        return new_baseline
    
    async def get_active_baseline(self, device_id: UUID) -> Optional[BaselineVersionModel]:
        """Get the active baseline for a device."""
        result = await self.db.execute(
            select(BaselineVersionModel).where(
                and_(
                    BaselineVersionModel.device_id == device_id,
                    BaselineVersionModel.is_active == True,
                )
            )
        )
        return result.scalar_one_or_none()
    
    # ===== Maintenance Recommendations =====
    
    async def generate_recommendations(self, device_id: UUID) -> List[MaintenanceRecommendationModel]:
        """Generate maintenance recommendations for a device."""
        recommendations = []
        
        # Get installed filters
        filters = await self.get_installed_filters(device_id)
        
        for filter_inst in filters:
            if filter_inst.lifecycle_state != FilterLifecycleState.INSTALLED:
                continue
            
            catalog = await self.db.get(FilterCatalogModel, filter_inst.catalog_id)
            if not catalog:
                continue
            
            # Time-based recommendation
            if catalog.rated_service_interval_days:
                age_days = (datetime.utcnow() - filter_inst.installation_date).days
                if age_days >= catalog.rated_service_interval_days * 0.9:
                    severity = "warning" if age_days < catalog.rated_service_interval_days else "critical"
                    rec = MaintenanceRecommendationModel(
                        device_id=device_id,
                        filter_instance_id=filter_inst.id,
                        trigger="time_based",
                        severity=severity,
                        evidence={"age_days": age_days, "rated_days": catalog.rated_service_interval_days},
                        urgency_days=max(0, catalog.rated_service_interval_days - age_days),
                        recommended_action=f"Replace {catalog.product_name} filter (stage {filter_inst.stage_position})",
                    )
                    self.db.add(rec)
                    recommendations.append(rec)
            
            # Usage-based recommendation
            if catalog.rated_usage_volume_liters and filter_inst.cumulative_volume_liters > 0:
                usage_pct = filter_inst.cumulative_volume_liters / catalog.rated_usage_volume_liters * 100
                if usage_pct >= 90:
                    severity = "warning" if usage_pct < 100 else "critical"
                    rec = MaintenanceRecommendationModel(
                        device_id=device_id,
                        filter_instance_id=filter_inst.id,
                        trigger="usage_based",
                        severity=severity,
                        evidence={"usage_pct": usage_pct, "volume_liters": filter_inst.cumulative_volume_liters},
                        urgency_days=None,
                        recommended_action=f"Replace {catalog.product_name} filter (stage {filter_inst.stage_position}) - {usage_pct:.0f}% of rated capacity used",
                    )
                    self.db.add(rec)
                    recommendations.append(rec)
        
        # Calibration recommendations
        due_sensors = await self.get_calibration_due(device_id)
        for sensor in due_sensors:
            rec = MaintenanceRecommendationModel(
                device_id=device_id,
                trigger="calibration_due",
                severity="warning" if sensor["status"] == "due_soon" else "critical",
                evidence=sensor,
                urgency_days=sensor.get("days_overdue"),
                recommended_action=f"Calibrate {sensor['sensor_type']} sensor ({sensor['status']})",
            )
            self.db.add(rec)
            recommendations.append(rec)
        
        await self.db.commit()
        
        # Refresh all recommendations
        for rec in recommendations:
            await self.db.refresh(rec)
        
        return recommendations
    
    # ===== Notification Integration =====
    
    async def _enqueue_maintenance_notification(
        self,
        device_id: UUID,
        event_type: MaintenanceEventType,
        message: str,
    ) -> None:
        """Enqueue a maintenance notification."""
        # Get provider configs for this device
        from app.models.notification import NotificationProviderConfig, NotificationChannel
        result = await self.db.execute(
            select(NotificationProviderConfig).where(
                and_(
                    NotificationProviderConfig.device_id == device_id,
                    NotificationProviderConfig.enabled == True,
                )
            )
        )
        configs = result.scalars().all()
        
        for config in configs:
            recipient = config.config.get("recipient") or config.config.get("email") or config.config.get("url")
            if not recipient:
                continue
            
            await self.notification_service.create_notification(
                alert=None,  # Maintenance notifications don't have alerts
                channel=config.channel,
                recipient=recipient,
                provider=config.provider,
                template_name="maintenance_event",
                template_data={
                    "event_type": event_type.value,
                    "message": message,
                    "device_id": str(device_id),
                    "timestamp": datetime.utcnow().isoformat(),
                },
                subject=f"Maintenance: {event_type.value}",
                dedupe_key=f"maintenance:{device_id}:{event_type.value}:{datetime.utcnow().date()}",
            )
    
    async def _enqueue_calibration_notification(
        self,
        device_id: UUID,
        sensor_type: str,
        notification_type: str,
    ) -> None:
        """Enqueue a calibration notification."""
        from app.models.notification import NotificationProviderConfig
        result = await self.db.execute(
            select(NotificationProviderConfig).where(
                and_(
                    NotificationProviderConfig.device_id == device_id,
                    NotificationProviderConfig.enabled == True,
                )
            )
        )
        configs = result.scalars().all()
        
        for config in configs:
            recipient = config.config.get("recipient") or config.config.get("email") or config.config.get("url")
            if not recipient:
                continue
            
            await self.notification_service.create_notification(
                alert=None,
                channel=config.channel,
                recipient=recipient,
                provider=config.provider,
                template_name=f"calibration_{notification_type}",
                template_data={
                    "sensor_type": sensor_type,
                    "device_id": str(device_id),
                    "timestamp": datetime.utcnow().isoformat(),
                },
                subject=f"Calibration {notification_type.replace('_', ' ').title()}: {sensor_type}",
                dedupe_key=f"calibration:{device_id}:{sensor_type}:{notification_type}:{datetime.utcnow().date()}",
            )
    
    async def _enqueue_verification_notification(
        self,
        device_id: UUID,
        passed: bool,
        failure_reasons: List[str],
    ) -> None:
        """Enqueue a verification notification."""
        from app.models.notification import NotificationProviderConfig
        result = await self.db.execute(
            select(NotificationProviderConfig).where(
                and_(
                    NotificationProviderConfig.device_id == device_id,
                    NotificationProviderConfig.enabled == True,
                )
            )
        )
        configs = result.scalars().all()
        
        for config in configs:
            recipient = config.config.get("recipient") or config.config.get("email") or config.config.get("url")
            if not recipient:
                continue
            
            await self.notification_service.create_notification(
                alert=None,
                channel=config.channel,
                recipient=recipient,
                provider=config.provider,
                template_name="verification_passed" if passed else "verification_failed",
                template_data={
                    "passed": passed,
                    "failure_reasons": failure_reasons,
                    "device_id": str(device_id),
                    "timestamp": datetime.utcnow().isoformat(),
                },
                subject=f"Verification {'Passed' if passed else 'Failed'} - Device {device_id}",
                dedupe_key=f"verification:{device_id}:{datetime.utcnow().isoformat()}",
            )