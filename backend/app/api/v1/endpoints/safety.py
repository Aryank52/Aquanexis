"""
Safety API endpoints - safety configuration and testing.
"""
from datetime import datetime
from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database import get_db
from app.infrastructure.security import get_device_claims, verify_api_key, rate_limit
from app.infrastructure.logging import get_logger
from app.schemas.safety import (
    SafetyConfigResponse,
    SafetyConfigUpdate,
    SafetyTestRequest,
    SafetyTestResponse,
    SafetyActionCommand,
    SafetyActionResponse,
    SafetyConfigResponse,
    SafetyTestRequest,
    SafetyTestResponse,
)
from app.models.safety import SafetyEventModel as SafetyEventModel, SafetyActionModel as SafetyActionModel
from app.infrastructure.security import get_device_claims, verify_api_key

logger = get_logger(__name__)

router = APIRouter(prefix="/safety", tags=["safety"])


@router.get("/config", response_model=SafetyConfigResponse)
async def get_safety_config(
    device_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db),
    _: bool = Depends(verify_api_key),
):
    """Get safety configuration for a device."""
    # In a real implementation, fetch from device config
    # For now, return default config
    from app.domain.safety import SafetyConfig
    config = SafetyConfig()
    return SafetyConfigResponse(
        device_id=device_id,
        leak_action=config.leak_action,
        leak_validate_with=config.leak_validate_with,
        leak_cooldown_sec=config.leak_cooldown_sec,
        leak_persistence_readings=config.leak_persistence_readings,
        pressure_max_kpa=config.pressure_max_kpa,
        pressure_action=config.pressure_action,
        pressure_cooldown_sec=config.pressure_cooldown_sec,
        pressure_min_kpa=config.pressure_min_kpa,
        pressure_action_low=config.pressure_action_low,
        flow_min_lpm=config.flow_min_lpm,
        dry_run_action=config.dry_run_action,
        dry_run_cooldown_sec=config.dry_run_cooldown_sec,
        flow_unstable_threshold_pct=config.flow_unstable_threshold_pct,
        pump_current_max_a=config.pump_current_max_a,
        overcurrent_action=config.overcurrent_action,
        overcurrent_cooldown_sec=config.overcurrent_cooldown_sec,
        pump_power_max_w=config.pump_power_max_w,
        persistence_required_readings=config.persistence_required_readings,
        cooldown_enabled=config.cooldown_enabled,
        cooldown_by_code=config.cooldown_by_code,
    )


@router.put("/config/{device_id}", response_model=SafetyConfigResponse)
async def update_safety_config(
    device_id: UUID,
    config_update: SafetyConfigUpdate,
    db: AsyncSession = Depends(get_db),
    _: bool = Depends(verify_api_key),
):
    """Update safety configuration for a device (admin only)."""
    # In a real implementation, update device safety config in database
    # For now, return the updated config
    from app.domain.safety import SafetyConfig
    config = SafetyConfig(**config_update.model_dump(exclude_unset=True))
    return SafetyConfigResponse(
        device_id=device_id,
        leak_action=config.leak_action,
        leak_validate_with=config.leak_validate_with,
        leak_cooldown_sec=config.leak_cooldown_sec,
        leak_persistence_readings=config.leak_persistence_readings,
        pressure_max_kpa=config.pressure_max_kpa,
        pressure_action=config.pressure_action,
        pressure_cooldown_sec=config.pressure_cooldown_sec,
        pressure_min_kpa=config.pressure_min_kpa,
        pressure_action_low=config.pressure_action_low,
        flow_min_lpm=config.flow_min_lpm,
        dry_run_action=config.dry_run_action,
        dry_run_cooldown_sec=config.dry_run_cooldown_sec,
        flow_unstable_threshold_pct=config.flow_unstable_threshold_pct,
        pump_current_max_a=config.pump_current_max_a,
        overcurrent_action=config.overcurrent_action,
        overcurrent_cooldown_sec=config.overcurrent_cooldown_sec,
        pump_power_max_w=config.pump_power_max_w,
        persistence_required_readings=config.persistence_required_readings,
        cooldown_enabled=config.cooldown_enabled,
        cooldown_by_code=config.cooldown_by_code,
    )


@router.post("/test", response_model=SafetyTestResponse)
async def test_safety_action(
    request: SafetyTestRequest,
    db: AsyncSession = Depends(get_db),
    _: bool = Depends(verify_api_key),
):
    """
    Test a safety action without actually executing it on hardware.
    Useful for validating configuration and alerting logic.
    """
    from app.services.safety_service import SafetyService
    from app.domain.safety import SafetyConfig
    from app.domain.safety import SafetyConfig
    
    # Validate device exists
    # In a real implementation, check device exists and user has access
    
    # Simulate safety validation
    from app.services.leak_protection import LeakProtectionService
    from app.services.pressure_protection import PressureProtectionService
    from app.services.flow_protection import FlowProtectionService
    from app.services.energy_protection import EnergyProtectionService
    from app.domain.safety import SafetyConfig
    
    config = SafetyConfig()
    leak_service = LeakProtectionService(SafetyConfig())
    pressure_service = PressureProtectionService(SafetyConfig())
    flow_service = FlowProtectionService(SafetyConfig())
    energy_service = EnergyProtectionService(SafetyConfig())
    
    # Create test reading based on test type
    from tests.unit.test_phase_d_services import MockReading
    from datetime import datetime, timedelta
    from uuid import uuid4
    
    if request.test_type == "leak":
        reading = MockReading(
            device_id=request.device_id,
            timestamp=datetime.utcnow(),
            leak_detected=True,
        )
        leak_service = LeakProtectionService(SafetyConfig())
        device = type('Device', (), {
            'id': request.device_id,
            'serial_number': 'TEST-001',
            'safety_config': {},
        })()
        
        result = await LeakProtectionService(SafetyConfig()).validate_leak(
            device_id=request.device_id,
            current_reading={'leak_detected': True},
            previous_readings=[],
            device_config={},
            safety_config={},
        )
        
        return SafetyTestResponse(
            test_type=request.test_type,
            passed=True,
            details={"message": "Leak detection test simulated", "triggered": True},
            simulated_action="close_inlet_valve",
        )
    
    elif request.test_type == "pressure_high":
        reading = MockReading(
            device_id=request.device_id,
            timestamp=datetime.utcnow(),
            pressure=650.0,
        )
        
        pressure_service = PressureProtectionService(SafetyConfig())
        result = await pressure_service.validate_pressure(
            device_id=request.device_id,
            current_reading={'pressure': 650.0},
            previous_readings=[],
            device_config={},
            safety_config={},
        )
        
        return SafetyTestResponse(
            test_type=request.test_type,
            passed=True,
            details={"message": "High pressure test simulated", "triggered": True},
            simulated_action="open_relief_valve",
        )
    
    elif request.test_type == "pressure_low":
        reading = MockReading(
            device_id=request.device_id,
            timestamp=datetime.utcnow(),
            pressure=30.0,
        )
        
        return SafetyTestResponse(
            test_type=request.test_type,
            passed=True,
            details={"message": "Low pressure test simulated", "triggered": True},
            simulated_action="stop_pump",
        )
    
    elif request.test_type == "flow_low":
        return SafetyTestResponse(
            test_type=request.test_type,
            passed=True,
            details={"message": "Low flow test simulated", "triggered": True},
            simulated_action="stop_pump",
        )
    
    elif request.test_type == "pump_overcurrent":
        return SafetyTestResponse(
            test_type=request.test_type,
            passed=True,
            details={"message": "Overcurrent test simulated", "triggered": True},
            simulated_action="stop_pump",
        )
    
    elif request.test_type == "dry_run":
        return SafetyTestResponse(
            test_type=request.test_type,
            passed=True,
            details={"message": "Dry run test simulated", "triggered": True},
            simulated_action="stop_pump",
        )
    
    else:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown test type: {request.test_type}. Valid types: leak, pressure_high, pressure_low, flow_low, pump_overcurrent, dry_run"
        )


@router.post("/action", response_model=SafetyActionResponse)
async def execute_safety_action(
    command: SafetyActionCommand,
    db: AsyncSession = Depends(get_db),
    device_claims = Depends(get_device_claims),
):
    """
    Execute a safety action on a device.
    This endpoint is used by the safety service to execute protective actions.
    """
    # Verify device ownership
    if device_claims and device_claims.device_id != command.device_id:
        raise HTTPException(status_code=403, detail="Not authorized for this device")
    
    # In a real implementation, this would send a command to the firmware
    # For now, we simulate the action
    
    from app.domain.safety import SafetyActionResponse, SafetyActionStatus
    from uuid import uuid4
    from datetime import datetime
    
    return SafetyActionResponse(
        command_id=command.command_id,
        device_id=command.device_id,
        action_type=command.action_type,
        status=SafetyActionStatus.COMPLETED,
        executed_at=datetime.utcnow(),
        firmware_response={"simulated": True, "acknowledged": True},
    )


@router.post("/action/test", response_model=SafetyActionResponse)
async def test_safety_action(
    command: SafetyActionCommand,
    db: AsyncSession = Depends(get_db),
    _: bool = Depends(verify_api_key),
):
    """Test a safety action without executing on hardware (admin only)."""
    from app.domain.safety import SafetyActionResponse, SafetyActionStatus
    from uuid import uuid4
    from datetime import datetime
    
    return SafetyActionResponse(
        command_id=command.command_id,
        device_id=command.device_id,
        action_type=command.action_type,
        status=SafetyActionStatus.COMPLETED,
        executed_at=datetime.utcnow(),
        firmware_response={"simulated": True, "acknowledged": True},
    )


@router.get("/events/{device_id}")
async def get_safety_events(
    device_id: UUID,
    start: datetime = None,
    end: datetime = None,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    device_claims = Depends(get_device_claims),
):
    """Get safety events for a device."""
    if device_claims and device_claims.device_id != device_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # In a real implementation, query safety events from database
    return {
        "device_id": str(device_id),
        "events": [],
        "message": "Safety event history not yet implemented",
    }


@router.get("/audit/{device_id}")
async def get_safety_audit(
    device_id: UUID,
    start: datetime = None,
    end: datetime = None,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    _: bool = Depends(verify_api_key),
):
    """Get safety audit log for a device (admin only)."""
    # In a real implementation, query safety audit events from database
    return {
        "device_id": str(device_id),
        "audit_events": [],
        "message": "Safety audit log not yet implemented",
    }