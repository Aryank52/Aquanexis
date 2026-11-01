"""
Telemetry ingestion and query endpoints.
"""
from datetime import datetime, timedelta
from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy import select, func, desc, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database import get_db
from app.infrastructure.security import get_device_claims, verify_api_key, rate_limit
from app.infrastructure.logging import get_logger
from app.infrastructure.websocket import ws_manager
from app.domain.devices import Device, DeviceStatus, DeviceSensorConfig, SafetyConfig
from app.domain.readings import (
    SensorReading,
    TelemetryPayload,
    BatchTelemetryPayload,
    BatchTelemetryResult,
)
from app.domain.quality import QualityValidator, quality_validator
from app.domain.water_quality import compute_aquascore, compute_trends, detect_anomalies
from app.domain.alerts import Alert, ALERT_TRANSITIONS, ALERT_CODES, AlertSeverity, AlertStatus
from app.schemas.telemetry import (
    TelemetryPayload as TelemetryPayloadSchema,
    BatchTelemetryPayload as BatchTelemetryPayloadSchema,
    TelemetryIngestResponse,
    BatchTelemetryResult,
    SensorReadingResponse,
    TelemetryHistoryQuery,
    TelemetryHistoryResponse,
    DeviceStatusResponse,
    DeviceCreate,
    DeviceUpdate,
    DeviceResponse,
    QualityFlags,
)
from app.models.device import Device as DeviceModel
from app.models.reading import SensorReading as SensorReadingModel
from app.models.alert import Alert as AlertModel, AlertSeverity as AlertSeverityModel, AlertStatus as AlertStatusModel

logger = get_logger(__name__)

router = APIRouter(prefix="/telemetry", tags=["telemetry"])

# In-memory cache for latest readings (in production, use Redis)
_latest_readings_cache: dict[UUID, SensorReadingModel] = {}


# ===== Device Endpoints =====

@router.post("/devices", response_model=DeviceResponse, status_code=status.HTTP_201_CREATED)
async def create_device(
    device_data: DeviceCreate,
    db: AsyncSession = Depends(get_db),
    _: bool = Depends(verify_api_key)
):
    """Register a new device (admin only)."""
    existing = await db.execute(
        select(DeviceModel).where(DeviceModel.serial_number == device_data.serial_number)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Device with serial number {device_data.serial_number} already exists"
        )
    
    sensor_config = device_data.sensor_config.model_dump()
    safety_config = device_data.safety_config.model_dump()
    
    device = DeviceModel(
        serial_number=device_data.serial_number,
        display_name=device_data.display_name,
        model=device_data.model,
        firmware_version=device_data.firmware_version,
        sensor_config=sensor_config,
        safety_config=safety_config,
        calibration={},
        capabilities=device_data.capabilities,
        status=DeviceStatus.OFFLINE.value,
    )
    
    db.add(device)
    await db.commit()
    await db.refresh(device)
    
    logger.info("device_created", device_id=str(device.id), serial=device.serial_number)
    return device


@router.get("/devices", response_model=List[DeviceResponse])
async def list_devices(
    limit: int = 100,
    offset: int = 0,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    _: bool = Depends(verify_api_key)
):
    """List all devices (admin only)."""
    query = select(DeviceModel).offset(offset).limit(limit)
    if status:
        query = query.where(DeviceModel.status == status)
    query = query.order_by(DeviceModel.created_at.desc())
    
    result = await db.execute(query)
    devices = result.scalars().all()
    return devices


@router.get("/devices/{device_id}", response_model=DeviceResponse)
async def get_device(
    device_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: bool = Depends(verify_api_key)
):
    """Get device details (admin only)."""
    device = await db.get(DeviceModel, device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    return device


@router.patch("/devices/{device_id}", response_model=DeviceResponse)
async def update_device(
    device_id: UUID,
    device_update: DeviceUpdate,
    db: AsyncSession = Depends(get_db),
    _: bool = Depends(verify_api_key)
):
    """Update device configuration (admin only)."""
    device = await db.get(DeviceModel, device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    update_data = device_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if field in ("sensor_config", "safety_config") and value is not None:
            setattr(device, field, value.model_dump())
        else:
            setattr(device, field, value)
    
    device.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(device)
    
    logger.info("device_updated", device_id=str(device_id))
    return device


# ===== Alert Evaluation =====

async def evaluate_alerts(
    device: DeviceModel,
    reading: SensorReadingModel,
    quality_flags: dict,
    db: AsyncSession
) -> List[AlertModel]:
    """Evaluate alert rules for a new reading and create alerts if needed."""
    new_alerts = []
    
    safety_config = device.safety_config or {}
    
    # Check leak
    if reading.leak_detected:
        existing = await db.execute(
            select(AlertModel).where(
                and_(
                    AlertModel.device_id == device.id,
                    AlertModel.alert_code == "leak_detected",
                    AlertModel.status.in_([AlertStatusModel.DETECTED, AlertStatusModel.OPEN, AlertStatusModel.ACKNOWLEDGED, AlertStatusModel.SNOOZED])
                )
            )
        )
        if not existing.scalar_one_or_none():
            alert = AlertModel(
                device_id=device.id,
                alert_code="leak_detected",
                severity=AlertSeverityModel.CRITICAL,
                status=AlertStatusModel.DETECTED,
                title="Leak Detected",
                message="Leak sensor triggered - water accumulation detected",
                trigger_source="leak_sensor",
                trigger_value={"leak": True},
                threshold_value={"leak": False},
                evidence={"leak_sensor": True, "reading_id": reading.id},
                rule_version="1.0",
            )
            db.add(alert)
            new_alerts.append(alert)
    
    # Check pressure thresholds
    pressure_max = safety_config.get("pressure_max_kpa", 600.0)
    if reading.pressure and reading.pressure > pressure_max:
        existing = await db.execute(
            select(AlertModel).where(
                and_(
                    AlertModel.device_id == device.id,
                    AlertModel.alert_code == "pressure_high",
                    AlertModel.status.in_([AlertStatusModel.DETECTED, AlertStatusModel.OPEN, AlertStatusModel.ACKNOWLEDGED, AlertStatusModel.SNOOZED])
                )
            )
        )
        if not existing.scalar_one_or_none():
            alert = AlertModel(
                device_id=device.id,
                alert_code="pressure_high",
                severity=AlertSeverityModel.CRITICAL,
                status=AlertStatusModel.DETECTED,
                title="Excessive Pressure",
                message=f"Inlet pressure {reading.pressure:.1f} kPa exceeds maximum {pressure_max} kPa",
                trigger_source="pressure_sensor",
                trigger_value={"pressure_kpa": reading.pressure},
                threshold_value={"max_pressure_kpa": pressure_max},
                evidence={"pressure_kpa": reading.pressure, "reading_id": reading.id},
                rule_version="1.0",
            )
            db.add(alert)
            new_alerts.append(alert)
    
    # Check low pressure
    if reading.pressure and reading.pressure < 50:
        existing = await db.execute(
            select(AlertModel).where(
                and_(
                    AlertModel.device_id == device.id,
                    AlertModel.alert_code == "pressure_low",
                    AlertModel.status.in_([AlertStatusModel.DETECTED, AlertStatusModel.OPEN, AlertStatusModel.ACKNOWLEDGED, AlertStatusModel.SNOOZED])
                )
            )
        )
        if not existing.scalar_one_or_none():
            alert = AlertModel(
                device_id=device.id,
                alert_code="pressure_low",
                severity=AlertSeverityModel.WARNING,
                status=AlertStatusModel.DETECTED,
                title="Low Pressure",
                message=f"Inlet pressure {reading.pressure:.1f} kPa below minimum threshold",
                trigger_source="pressure_sensor",
                trigger_value={"pressure_kpa": reading.pressure},
                threshold_value={"min_pressure_kpa": 50},
                evidence={"pressure_kpa": reading.pressure, "reading_id": reading.id},
                rule_version="1.0",
            )
            db.add(alert)
            new_alerts.append(alert)
    
    # Check flow
    flow_min = safety_config.get("flow_min_lpm", 0.1)
    if reading.flow is not None and reading.flow < flow_min:
        existing = await db.execute(
            select(AlertModel).where(
                and_(
                    AlertModel.device_id == device.id,
                    AlertModel.alert_code == "flow_low",
                    AlertModel.status.in_([AlertStatusModel.DETECTED, AlertStatusModel.OPEN, AlertStatusModel.ACKNOWLEDGED, AlertStatusModel.SNOOZED])
                )
            )
        )
        if not existing.scalar_one_or_none():
            alert = AlertModel(
                device_id=device.id,
                alert_code="flow_low",
                severity=AlertSeverityModel.WARNING,
                status=AlertStatusModel.DETECTED,
                title="Low Flow",
                message=f"Flow rate {reading.flow:.2f} L/min below minimum {flow_min} L/min",
                trigger_source="flow_sensor",
                trigger_value={"flow_lpm": reading.flow},
                threshold_value={"min_flow_lpm": flow_min},
                evidence={"flow_lpm": reading.flow, "reading_id": reading.id},
                rule_version="1.0",
            )
            db.add(alert)
            new_alerts.append(alert)
    
    # Check pump current
    pump_max = safety_config.get("pump_current_max_a", 2.5)
    if reading.pump_current and reading.pump_current > pump_max:
        existing = await db.execute(
            select(AlertModel).where(
                and_(
                    AlertModel.device_id == device.id,
                    AlertModel.alert_code == "pump_overcurrent",
                    AlertModel.status.in_([AlertStatusModel.DETECTED, AlertStatusModel.OPEN, AlertStatusModel.ACKNOWLEDGED, AlertStatusModel.SNOOZED])
                )
            )
        )
        if not existing.scalar_one_or_none():
            alert = AlertModel(
                device_id=device.id,
                alert_code="pump_overcurrent",
                severity=AlertSeverityModel.CRITICAL,
                status=AlertStatusModel.DETECTED,
                title="Pump Overcurrent",
                message=f"Pump current {reading.pump_current:.2f} A exceeds maximum {pump_max} A",
                trigger_source="pump_current_sensor",
                trigger_value={"current_a": reading.pump_current},
                threshold_value={"max_current_a": pump_max},
                evidence={"current_a": reading.pump_current, "reading_id": reading.id},
                rule_version="1.0",
            )
            db.add(alert)
            new_alerts.append(alert)
    
    # Check water quality (TDS)
    if reading.tds and reading.tds > 500:
        existing = await db.execute(
            select(AlertModel).where(
                and_(
                    AlertModel.device_id == device.id,
                    AlertModel.alert_code == "water_quality_degraded",
                    AlertModel.status.in_([AlertStatusModel.DETECTED, AlertStatusModel.OPEN, AlertStatusModel.ACKNOWLEDGED, AlertStatusModel.SNOOZED])
                )
            )
        )
        if not existing.scalar_one_or_none():
            alert = AlertModel(
                device_id=device.id,
                alert_code="water_quality_degraded",
                severity=AlertSeverityModel.WARNING,
                status=AlertStatusModel.DETECTED,
                title="Water Quality Degraded",
                message=f"TDS {reading.tds:.1f} ppm exceeds recommended limit",
                trigger_source="tds_sensor",
                trigger_value={"tds_ppm": reading.tds},
                threshold_value={"tds_limit_ppm": 500},
                evidence={"tds_ppm": reading.tds, "reading_id": reading.id},
                rule_version="1.0",
            )
            db.add(alert)
            new_alerts.append(alert)
    
    # Check tank level
    if reading.tank_level is not None and reading.tank_level < 10:
        existing = await db.execute(
            select(AlertModel).where(
                and_(
                    AlertModel.device_id == device.id,
                    AlertModel.alert_code == "tank_level_low",
                    AlertModel.status.in_([AlertStatusModel.DETECTED, AlertStatusModel.OPEN, AlertStatusModel.ACKNOWLEDGED, AlertStatusModel.SNOOZED])
                )
            )
        )
        if not existing.scalar_one_or_none():
            alert = AlertModel(
                device_id=device.id,
                alert_code="tank_level_low",
                severity=AlertSeverityModel.WARNING,
                status=AlertStatusModel.DETECTED,
                title="Tank Level Low",
                message=f"Tank level at {reading.tank_level:.1f}%",
                trigger_source="tank_level_sensor",
                trigger_value={"level_percent": reading.tank_level},
                threshold_value={"min_level_percent": 10},
                evidence={"level_percent": reading.tank_level, "reading_id": reading.id},
                rule_version="1.0",
            )
            db.add(alert)
            new_alerts.append(alert)
    
    if new_alerts:
        await db.commit()
        for alert in new_alerts:
            await db.refresh(alert)
    
    return new_alerts


# ===== Telemetry Ingestion =====

@router.post("", response_model=TelemetryIngestResponse)
async def ingest_telemetry(
    payload: TelemetryPayloadSchema,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    device_claims = Depends(get_device_claims),
    _: None = Depends(rate_limit)
):
    """
    Ingest single telemetry reading from device.
    Requires device JWT authentication.
    """
    # Verify device owns the payload
    if device_claims.device_id != payload.device_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Device ID mismatch"
        )
    
    device = await db.get(DeviceModel, payload.device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    # Check for duplicate sequence
    if payload.sequence is not None:
        if quality_validator.check_duplicate_sequence(payload.device_id, payload.sequence):
            logger.warning("duplicate_sequence", device_id=str(payload.device_id), sequence=payload.sequence)
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Duplicate sequence number"
            )
    
    # Validate readings
    domain_payload = TelemetryPayload(
        device_id=payload.device_id,
        timestamp=payload.timestamp,
        sequence=payload.sequence,
        firmware_version=payload.firmware_version,
        readings=payload.readings,
    )
    
    # Get previous reading for rate validation
    prev_reading = _latest_readings_cache.get(payload.device_id)
    prev_domain = None
    if prev_reading:
        prev_domain = SensorReading(
            id=prev_reading.id,
            device_id=prev_reading.device_id,
            timestamp=prev_reading.timestamp,
            ingestion_timestamp=prev_reading.received_at,
            sequence=prev_reading.sequence,
            tds=prev_reading.tds,
            conductivity=prev_reading.ec,
            ph=prev_reading.ph,
            turbidity=prev_reading.turbidity,
            temperature=prev_reading.temperature,
            flow_rate=prev_reading.flow,
            inlet_pressure=prev_reading.pressure,
            outlet_pressure=prev_reading.outlet_pressure,
            tank_level=prev_reading.tank_level,
            leak=prev_reading.leak_detected,
            pump_current=prev_reading.pump_current,
            pump_power=prev_reading.pump_power,
            uv_state=prev_reading.uv_state,
        )
    
    # Convert device model to domain for validation
    domain_device = Device(
        id=device.id,
        serial_number=device.serial_number,
        display_name=device.display_name,
        model=device.model,
        firmware_version=device.firmware_version,
        sensor_config=DeviceSensorConfig(**device.sensor_config) if device.sensor_config else DeviceSensorConfig(),
        safety_config=SafetyConfig(**device.safety_config) if device.safety_config else SafetyConfig(),
        calibration=device.calibration or {},
        capabilities=device.capabilities or {},
        status=DeviceStatus(device.status),
        last_seen_at=device.last_seen,
    )
    
    # Validate
    quality_flags = quality_validator.validate(domain_device, domain_payload, prev_domain)
    overall_quality = quality_flags.overall()
    
    # Create reading model
    reading = SensorReadingModel(
        device_id=payload.device_id,
        timestamp=payload.timestamp,
        sequence=payload.sequence,
        tds=payload.readings.tds,
        ec=payload.readings.conductivity,
        ph=payload.readings.ph,
        turbidity=payload.readings.turbidity,
        temperature=payload.readings.temperature,
        flow=payload.readings.flow_rate,
        pressure=payload.readings.inlet_pressure,
        outlet_pressure=payload.readings.outlet_pressure,
        tank_level=payload.readings.tank_level,
        leak_detected=payload.readings.leak,
        pump_current=payload.readings.pump_current,
        pump_power=payload.readings.pump_power,
        permeate_flow=None,
        reject_flow=None,
        uv_state=payload.readings.uv_state,
        vibration=None,
        quality_flags=quality_flags.to_dict(),
        overall_quality=overall_quality,
    )
    
    db.add(reading)
    await db.commit()
    await db.refresh(reading)
    
    # Update cache
    _latest_readings_cache[payload.device_id] = reading
    
    # Update device last_seen and status
    device.last_seen = payload.timestamp
    device.status = DeviceStatus.ACTIVE.value
    await db.commit()
    
    # Update validator cache
    quality_validator.update_last_reading(SensorReading(
        id=reading.id,
        device_id=reading.device_id,
        timestamp=reading.timestamp,
        ingestion_timestamp=reading.received_at,
        sequence=reading.sequence,
        tds=reading.tds,
        conductivity=reading.ec,
        ph=reading.ph,
        turbidity=reading.turbidity,
        temperature=reading.temperature,
        flow_rate=reading.flow,
        inlet_pressure=reading.pressure,
        outlet_pressure=reading.outlet_pressure,
        tank_level=reading.tank_level,
        leak=reading.leak_detected,
        pump_current=reading.pump_current,
        pump_power=reading.pump_power,
        uv_state=reading.uv_state,
        quality_flags=quality_flags,
        overall_quality=overall_quality,
    ))
    
    # Evaluate alerts
    new_alerts = await evaluate_alerts(device, reading, quality_flags.to_dict(), db)
    
    # Broadcast telemetry update via WebSocket
    if new_alerts:
        for alert in new_alerts:
            await ws_manager.broadcast_alert(payload.device_id, {
                "id": str(alert.id),
                "alert_code": alert.alert_code,
                "severity": alert.severity.value,
                "status": alert.status.value,
                "title": alert.title,
                "message": alert.message,
            }, "alert.created")
    
    await ws_manager.broadcast_telemetry(payload.device_id, {
        "timestamp": payload.timestamp.isoformat(),
        "readings": payload.readings.model_dump(exclude_none=True),
        "quality": quality_flags.to_dict(),
        "overall_quality": overall_quality,
    })
    
    # Background derivation
    background_tasks.add_task(derive_and_persist, payload.device_id, reading.id)
    
    logger.info(
        "telemetry_ingested",
        device_id=str(payload.device_id),
        reading_id=reading.id,
        quality=overall_quality,
        sequence=payload.sequence,
        alerts_generated=len(new_alerts)
    )
    
    return TelemetryIngestResponse(
        accepted=True,
        reading_id=reading.id,
        quality=quality_flags,
        derived={"status": "processing"}
    )


@router.post("/batch", response_model=BatchTelemetryResult)
async def ingest_telemetry_batch(
    payload: BatchTelemetryPayloadSchema,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    device_claims = Depends(get_device_claims),
    _: None = Depends(rate_limit)
):
    """
    Ingest batch telemetry readings from device.
    Useful for devices with intermittent connectivity.
    """
    if device_claims.device_id != payload.device_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Device ID mismatch"
        )
    
    device = await db.get(DeviceModel, payload.device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    result = BatchTelemetryResult()
    domain_device = Device(
        id=device.id,
        serial_number=device.serial_number,
        display_name=device.display_name,
        model=device.model,
        firmware_version=device.firmware_version,
        sensor_config=DeviceSensorConfig(**device.sensor_config) if device.sensor_config else DeviceSensorConfig(),
        safety_config=SafetyConfig(**device.safety_config) if device.safety_config else SafetyConfig(),
        calibration=device.calibration or {},
        capabilities=device.capabilities or {},
        status=DeviceStatus(device.status),
        last_seen_at=device.last_seen,
    )
    
    # Get last reading for rate validation
    prev_domain = None
    prev_reading = _latest_readings_cache.get(payload.device_id)
    if prev_reading:
        prev_domain = SensorReading(
            id=prev_reading.id,
            device_id=prev_reading.device_id,
            timestamp=prev_reading.timestamp,
            ingestion_timestamp=prev_reading.received_at,
            sequence=prev_reading.sequence,
            tds=prev_reading.tds,
            conductivity=prev_reading.ec,
            ph=prev_reading.ph,
            turbidity=prev_reading.turbidity,
            temperature=prev_reading.temperature,
            flow_rate=prev_reading.flow,
            inlet_pressure=prev_reading.pressure,
            outlet_pressure=prev_reading.outlet_pressure,
            tank_level=prev_reading.tank_level,
            leak=prev_reading.leak_detected,
            pump_current=prev_reading.pump_current,
            pump_power=prev_reading.pump_power,
            uv_state=prev_reading.uv_state,
        )
    
    for item in payload.readings:
        try:
            # Check duplicate
            if item.sequence is not None:
                if quality_validator.check_duplicate_sequence(payload.device_id, item.sequence):
                    result.duplicates += 1
                    result.errors.append({"sequence": item.sequence, "error": "duplicate"})
                    continue
            
            # Validate
            domain_payload = TelemetryPayload(
                device_id=item.device_id,
                timestamp=item.timestamp,
                sequence=item.sequence,
                firmware_version=item.firmware_version,
                readings=item.readings,
            )
            
            quality_flags = quality_validator.validate(domain_device, domain_payload, prev_domain)
            overall_quality = quality_flags.overall()
            
            # Create reading
            reading = SensorReadingModel(
                device_id=item.device_id,
                timestamp=item.timestamp,
                sequence=item.sequence,
                tds=item.readings.tds,
                ec=item.readings.conductivity,
                ph=item.readings.ph,
                turbidity=item.readings.turbidity,
                temperature=item.readings.temperature,
                flow=item.readings.flow_rate,
                pressure=item.readings.inlet_pressure,
                outlet_pressure=item.readings.outlet_pressure,
                tank_level=item.readings.tank_level,
                leak_detected=item.readings.leak,
                pump_current=item.readings.pump_current,
                pump_power=item.readings.pump_power,
                permeate_flow=None,
                reject_flow=None,
                uv_state=item.readings.uv_state,
                vibration=None,
                quality_flags=quality_flags.to_dict(),
                overall_quality=overall_quality,
            )
            
            db.add(reading)
            result.accepted += 1
            prev_domain = SensorReading(
                id=0,  # Will be set after commit
                device_id=reading.device_id,
                timestamp=reading.timestamp,
                ingestion_timestamp=reading.received_at,
                sequence=reading.sequence,
                tds=reading.tds,
                conductivity=reading.ec,
                ph=reading.ph,
                turbidity=reading.turbidity,
                temperature=reading.temperature,
                flow_rate=reading.flow,
                inlet_pressure=reading.pressure,
                outlet_pressure=reading.outlet_pressure,
                tank_level=reading.tank_level,
                leak=reading.leak_detected,
                pump_current=reading.pump_current,
                pump_power=reading.pump_power,
                uv_state=reading.uv_state,
            )
            
        except Exception as e:
            result.invalid += 1
            result.errors.append({"sequence": item.sequence, "error": str(e)})
            logger.warning("batch_item_failed", sequence=item.sequence, error=str(e))
    
    await db.commit()
    
    # Update device last_seen
    if payload.readings:
        latest_ts = max(r.timestamp for r in payload.readings)
        device.last_seen = latest_ts
        device.status = DeviceStatus.ACTIVE.value
        await db.commit()
    
    logger.info(
        "telemetry_batch_ingested",
        device_id=str(payload.device_id),
        accepted=result.accepted,
        rejected=result.rejected,
        duplicates=result.duplicates,
        invalid=result.invalid
    )
    
    return result


# ===== Telemetry Query Endpoints =====

@router.get("/latest/{device_id}", response_model=SensorReadingResponse)
async def get_latest_telemetry(
    device_id: UUID,
    db: AsyncSession = Depends(get_db),
    device_claims = Depends(get_device_claims)
):
    """Get latest telemetry reading for a device."""
    cached = _latest_readings_cache.get(device_id)
    if cached:
        return SensorReadingResponse(
            id=cached.id,
            device_id=cached.device_id,
            timestamp=cached.timestamp,
            ingestion_timestamp=cached.received_at,
            sequence=cached.sequence,
            tds=cached.tds,
            conductivity=cached.ec,
            ph=cached.ph,
            turbidity=cached.turbidity,
            temperature=cached.temperature,
            flow_rate=cached.flow,
            inlet_pressure=cached.pressure,
            outlet_pressure=cached.outlet_pressure,
            tank_level=cached.tank_level,
            leak=cached.leak_detected,
            pump_current=cached.pump_current,
            pump_power=cached.pump_power,
            uv_state=cached.uv_state,
            quality=QualityFlags(**cached.quality_flags) if cached.quality_flags else QualityFlags(),
            overall_quality=cached.overall_quality,
        )
    
    result = await db.execute(
        select(SensorReadingModel)
        .where(SensorReadingModel.device_id == device_id)
        .order_by(desc(SensorReadingModel.timestamp))
        .limit(1)
    )
    reading = result.scalar_one_or_none()
    
    if not reading:
        raise HTTPException(status_code=404, detail="No telemetry found for device")
    
    _latest_readings_cache[device_id] = reading
    
    return SensorReadingResponse(
        id=reading.id,
        device_id=reading.device_id,
        timestamp=reading.timestamp,
        ingestion_timestamp=reading.received_at,
        sequence=reading.sequence,
        tds=reading.tds,
        conductivity=reading.ec,
        ph=reading.ph,
        turbidity=reading.turbidity,
        temperature=reading.temperature,
        flow_rate=reading.flow,
        inlet_pressure=reading.pressure,
        outlet_pressure=reading.outlet_pressure,
        tank_level=reading.tank_level,
        leak=reading.leak_detected,
        pump_current=reading.pump_current,
        pump_power=reading.pump_power,
        uv_state=reading.uv_state,
        quality=QualityFlags(**reading.quality_flags) if reading.quality_flags else QualityFlags(),
        overall_quality=reading.overall_quality,
    )


@router.get("/history/{device_id}", response_model=TelemetryHistoryResponse)
async def get_telemetry_history(
    device_id: UUID,
    start: datetime,
    end: datetime,
    interval: str = "1m",
    limit: int = 1000,
    sensors: Optional[List[str]] = None,
    db: AsyncSession = Depends(get_db),
    device_claims = Depends(get_device_claims)
):
    """Get historical telemetry with optional downsampling."""
    if start >= end:
        raise HTTPException(status_code=400, detail="Start must be before end")
    
    if (end - start).total_seconds() > 30 * 24 * 3600:
        raise HTTPException(status_code=400, detail="Maximum range is 30 days")
    
    query = select(SensorReadingModel).where(
        and_(
            SensorReadingModel.device_id == device_id,
            SensorReadingModel.timestamp >= start,
            SensorReadingModel.timestamp <= end
        )
    ).order_by(SensorReadingModel.timestamp)
    
    result = await db.execute(query)
    readings = result.scalars().all()
    
    if len(readings) > limit:
        readings = downsample_readings(readings, limit)
    
    series = {}
    sensor_fields = {
        "tds": "tds",
        "conductivity": "ec",
        "ph": "ph",
        "turbidity": "turbidity",
        "temperature": "temperature",
        "flow_rate": "flow",
        "inlet_pressure": "pressure",
        "outlet_pressure": "outlet_pressure",
        "tank_level": "tank_level",
        "leak": "leak_detected",
        "pump_current": "pump_current",
        "pump_power": "pump_power",
    }
    
    if sensors is None:
        sensors = [k for k, v in sensor_fields.items() if v is not None]
    
    for sensor in sensors:
        field = sensor_fields.get(sensor)
        if field:
            series[sensor] = [
                {"timestamp": r.timestamp.isoformat(), "value": getattr(r, field)}
                for r in readings if getattr(r, field) is not None
            ]
    
    return TelemetryHistoryResponse(
        device_id=device_id,
        interval=interval,
        series=series
    )


@router.get("/status/{device_id}", response_model=DeviceStatusResponse)
async def get_device_status(
    device_id: UUID,
    db: AsyncSession = Depends(get_db),
    device_claims = Depends(get_device_claims)
):
    """Get device status and latest reading."""
    device = await db.get(DeviceModel, device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    latest = await get_latest_telemetry(device_id, db, device_claims)
    
    sensor_health = {}
    if latest.quality:
        for k in latest.quality.__fields__.keys():
            sensor_health[k] = getattr(latest.quality, k).state
    
    return DeviceStatusResponse(
        device_id=device_id,
        status=device.status,
        last_seen_at=device.last_seen,
        last_reading=latest,
        sensor_health=sensor_health
    )


# ===== Helper Functions =====

def downsample_readings(readings: List[SensorReadingModel], target_count: int) -> List[SensorReadingModel]:
    """Downsample readings using simple decimation."""
    if len(readings) <= target_count:
        return readings
    
    step = len(readings) / target_count
    return [readings[int(i * step)] for i in range(target_count)]


async def derive_and_persist(device_id: UUID, reading_id: int):
    """Background task to compute derived values."""
    logger.info("derivation_started", device_id=str(device_id), reading_id=reading_id)
    # TODO: Compute AquaScore, trends, anomalies, FSI, FHI, RUL, diagnostics
    # TODO: Persist to water_quality_scores, filter_health, diagnostics, etc.
    logger.info("derivation_completed", device_id=str(device_id), reading_id=reading_id)