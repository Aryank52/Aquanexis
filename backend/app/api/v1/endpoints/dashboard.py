"""
Dashboard composite endpoint - combines all device data for the dashboard.
"""
from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, desc, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database import get_db
from app.infrastructure.logging import get_logger
from app.infrastructure.security import get_device_claims
from app.models.device import Device as DeviceModel
from app.models.reading import SensorReading as SensorReadingModel
from app.models.water_quality import WaterQualityScore as WaterQualityScoreModel
from app.models.filter_health import FilterHealth as FilterHealthModel
from app.models.purification_performance import PurificationPerformance as PPModel
from app.models.system_diagnostics import SystemDiagnostics as DiagnosticsModel
from app.models.alert import Alert as AlertModel, AlertSeverity as AlertSeverityModel, AlertStatus as AlertStatusModel
from app.schemas.telemetry import (
    DashboardData,
    DeviceResponse,
    SensorReadingResponse,
    WaterQualityResponse,
    FilterHealthResponse,
    DiagnosticsDataResponse,
    PurificationPerformanceResponse,
    AlertResponse,
    ParameterScore,
    TrendAnalysis,
    TrendPoint,
    AlertSeverity as AlertSeveritySchema,
    AlertStatus as AlertStatusSchema,
    QualityFlags,
    DeviceSensorConfig,
    SafetyConfig,
    DeviceStatus,
)
from app.domain.devices import Device, DeviceSensorConfig, SafetyConfig, DeviceStatus as DomainDeviceStatus
from app.domain.readings import SensorReading
from app.domain.quality import QualityFlags
from app.domain.alerts import AlertSeverity, AlertStatus
from app.domain.water_quality import compute_aquascore, compute_trends, detect_anomalies

from app.infrastructure.websocket import ws_manager

from app.api.v1.endpoints.telemetry import _latest_readings_cache, get_latest_telemetry

logger = get_logger(__name__)

router = APIRouter(prefix="/devices", tags=["dashboard"])


@router.get("/{device_id}/dashboard", response_model=DashboardData)
async def get_dashboard(
    device_id: UUID,
    db: AsyncSession = Depends(get_db),
    device_claims = Depends(get_device_claims)
):
    """Get composite dashboard data for a device."""
    # Verify device exists and user has access
    device = await db.get(DeviceModel, device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    # Get latest telemetry
    latest_telemetry = await get_latest_telemetry(device_id, db, device_claims)
    
    # Get water quality
    water_quality = None
    wq_result = await db.execute(
        select(WaterQualityScoreModel)
        .where(WaterQualityScoreModel.device_id == device_id)
        .order_by(desc(WaterQualityScoreModel.timestamp))
        .limit(1)
    )
    wq_model = wq_result.scalar_one_or_none()
    if wq_model:
        # Parse parameter scores
        param_scores = []
        if wq_model.tds_score is not None:
            param_scores.append(ParameterScore(
                parameter="tds",
                value=None,
                score=wq_model.tds_score,
                guideline_min=0,
                guideline_max=300,
                unit="ppm",
            ))
        if wq_model.ph_score is not None:
            param_scores.append(ParameterScore(
                parameter="ph",
                value=None,
                score=wq_model.ph_score,
                guideline_min=6.5,
                guideline_max=8.5,
                unit="",
            ))
        if wq_model.turbidity_score is not None:
            param_scores.append(ParameterScore(
                parameter="turbidity",
                value=None,
                score=wq_model.turbidity_score,
                guideline_min=0,
                guideline_max=1,
                unit="NTU",
            ))
        if wq_model.temp_score is not None:
            param_scores.append(ParameterScore(
                parameter="temperature",
                value=None,
                score=wq_model.temp_score,
                guideline_min=10,
                guideline_max=25,
                unit="°C",
            ))
        if wq_model.conductivity_score is not None:
            param_scores.append(ParameterScore(
                parameter="conductivity",
                value=None,
                score=wq_model.conductivity_score,
                guideline_min=0,
                guideline_max=500,
                unit="µS/cm",
            ))
        
        # Parse trends
        trends = {}
        if wq_model.trends:
            for param, trend_data in wq_model.trends.items():
                if trend_data:
                    trends[param] = TrendAnalysis(
                        parameter=param,
                        window=trend_data.get('window', '24h'),
                        direction=trend_data.get('direction', 'stable'),
                        magnitude=trend_data.get('magnitude', 0),
                        points=[TrendPoint(**p) for p in trend_data.get('points', [])],
                        slope_per_hour=trend_data.get('slope_per_hour', 0),
                    )
        
        # Parse anomaly flags
        anomaly_flags = {}
        if wq_model.anomaly_flags:
            for flag in wq_model.anomaly_flags:
                anomaly_flags[flag.get('parameter', '')] = flag.get('score', 0)
        
        water_quality = AquaScoreResponse(
            device_id=wq_model.device_id,
            timestamp=wq_model.timestamp,
            aquascore=wq_model.aquascore,
            parameter_scores=param_scores,
            trends=trends,
            anomaly_score=wq_model.anomaly_score,
            anomaly_flags=anomaly_flags,
            data_freshness_seconds=data_freshness_seconds,
            provenance="CALCULATED",
        )
    
    # Get filter health
    filter_health = None
    fh_result = await db.execute(
        select(FilterHealthModel)
        .where(FilterHealthModel.device_id == device_id)
        .order_by(desc(FilterHealthModel.timestamp))
        .limit(1)
    )
    fh_model = fh_result.scalar_one_or_none()
    if fh_model:
        filter_health = FilterHealthResponse(
            device_id=fh_model.device_id,
            timestamp=fh_model.timestamp,
            fsi=fh_model.fsi,
            fhi=fh_model.fhi,
            rul_days=fh_model.rul_days,
            rul_confidence_lower=fh_model.rul_confidence_lower,
            rul_confidence_upper=fh_model.rul_confidence_upper,
            model_name=fh_model.model_name,
            model_version=fh_model.model_version,
            dataset_version=fh_model.dataset_version,
            input_features=fh_model.input_features,
            explanation=fh_model.explanation,
            maintenance_band=fh_model.maintenance_band,
            confidence_level=fh_model.confidence_level,
        )
    
    # Get diagnostics
    diagnostics = None
    diag_result = await db.execute(
        select(DiagnosticsModel)
        .where(DiagnosticsModel.device_id == device_id)
        .order_by(desc(DiagnosticsModel.timestamp))
        .limit(1)
    )
    diag_model = diag_result.scalar_one_or_none()
    if diag_model:
        diagnostics = DiagnosticsDataResponse(
            device_id=diag_model.device_id,
            timestamp=diag_model.timestamp,
            pressure=diag_model.pressure_kpa,
            flow=diag_model.flow_lpm,
            leak=diag_model.leak_detected,
            tank=diag_model.tank_level_percent,
            pump=diag_model.pump_current_a,
        )
    
    # Get purification
    purification = None
    pp_result = await db.execute(
        select(PPModel)
        .where(PPModel.device_id == device_id)
        .order_by(desc(PPModel.timestamp))
        .limit(1)
    )
    pp_model = pp_result.scalar_one_or_none()
    if pp_model:
        purification = PurificationPerformanceResponse(
            device_id=pp_model.device_id,
            timestamp=pp_model.timestamp,
            rejection_rate=pp_model.rejection_rate,
            recovery_ratio=pp_model.recovery_ratio,
            permeate_quality=pp_model.permeate_quality,
            feed_quality=pp_model.feed_quality,
            efficiency=pp_model.efficiency,
        )
    
    # Get active alert
    active_alert = None
    alert_result = await db.execute(
        select(AlertModel)
        .where(
            and_(
                AlertModel.device_id == device_id,
                AlertModel.status.in_([AlertStatusModel.DETECTED, AlertStatusModel.OPEN, AlertStatusModel.ACKNOWLEDGED, AlertStatusModel.SNOOZED])
            )
        )
        .order_by(desc(AlertModel.created_at))
        .limit(1)
    )
    alert_model = alert_result.scalar_one_or_none()
    if alert_model:
        active_alert = AlertResponse(
            id=alert_model.id,
            device_id=alert_model.device_id,
            alert_code=alert_model.alert_code,
            severity=AlertSeveritySchema(alert_model.severity.value),
            status=AlertStatusSchema(alert_model.status.value),
            title=alert_model.title,
            message=alert_model.message,
            trigger_source=alert_model.trigger_source,
            trigger_value=alert_model.trigger_value,
            threshold_value=alert_model.threshold_value,
            evidence=alert_model.evidence or {},
            created_at=alert_model.created_at,
            acknowledged_at=alert_model.acknowledged_at,
            snoozed_until=alert_model.snoozed_until,
            resolved_at=alert_model.resolved_at,
            auto_cleared_at=alert_model.auto_cleared_at,
            created_by=alert_model.created_by,
            acknowledged_by=alert_model.acknowledged_by,
            resolved_by=alert_model.resolved_by,
        )
    
    # Calculate data freshness
    data_freshness_seconds = 0
    latest_telemetry = await get_latest_telemetry(device_id, db, device_claims)
    
    latest_telemetry_response = None
    if latest_telemetry:
        latest_telemetry_response = SensorReadingResponse(
            id=latest_telemetry.id,
            device_id=latest_telemetry.device_id,
            timestamp=latest_telemetry.timestamp,
            ingestion_timestamp=latest_telemetry.received_at,
            sequence=latest_telemetry.sequence,
            tds=latest_telemetry.tds,
            conductivity=latest_telemetry.ec,
            ph=latest_telemetry.ph,
            turbidity=latest_telemetry.turbidity,
            temperature=latest_telemetry.temperature,
            flow_rate=latest_telemetry.flow,
            inlet_pressure=latest_telemetry.pressure,
            outlet_pressure=latest_telemetry.outlet_pressure,
            tank_level=latest_telemetry.tank_level,
            leak=latest_telemetry.leak_detected,
            pump_current=latest_telemetry.pump_current,
            pump_power=latest_telemetry.pump_power,
            uv_state=latest_telemetry.uv_state,
            quality=QualityFlags(**latest_telemetry.quality_flags) if latest_telemetry.quality_flags else QualityFlags(),
            overall_quality=latest_telemetry.overall_quality,
            provenance="SIMULATED",
        )
        
        if latest_telemetry.ingestion_timestamp:
            data_freshness_seconds = int((datetime.utcnow() - latest_telemetry.ingestion_timestamp).total_seconds())
        else:
            data_freshness_seconds = 0
    else:
        data_freshness_seconds = 0
    
    # Get device response
    device_response = DeviceResponse(
        id=device.id,
        serial_number=device.serial_number,
        display_name=device.display_name,
        model=device.model,
        firmware_version=device.firmware_version,
        sensor_config=DeviceSensorConfig(**device.sensor_config) if device.sensor_config else DeviceSensorConfig(),
        safety_config=SafetyConfig(**device.safety_config) if device.safety_config else SafetyConfig(),
        status=DeviceStatus(device.status),
        last_seen=device.last_seen,
        created_at=device.created_at,
        updated_at=device.updated_at,
    )
    
    return DashboardData(
        device=device_response,
        latest_telemetry=latest_telemetry_response,
        water_quality=water_quality,
        filter_health=filter_health,
        diagnostics=diagnostics,
        purification=purification,
        active_alert=active_alert,
        data_freshness_seconds=data_freshness_seconds,
    )


@router.get("/{device_id}/dashboard", response_model=DashboardData)
async def get_dashboard(
    device_id: UUID,
    db: AsyncSession = Depends(get_db),
    device_claims = Depends(get_device_claims)
):
    """Get composite dashboard data for a device."""
    # Verify device exists and user has access
    device = await db.get(DeviceModel, device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    # Get latest telemetry
    latest_telemetry = await get_latest_telemetry(device_id, db, device_claims)
    
    # Get water quality
    water_quality = None
    wq_result = await db.execute(
        select(WaterQualityScoreModel)
        .where(WaterQualityScoreModel.device_id == device_id)
        .order_by(desc(WaterQualityScoreModel.timestamp))
        .limit(1)
    )
    wq_model = wq_result.scalar_one_or_none()
    if wq_model:
        # Parse parameter scores
        param_scores = []
        if wq_model.tds_score is not None:
            param_scores.append(ParameterScore(
                parameter="tds",
                value=None,
                score=wq_model.tds_score,
                guideline_min=0,
                guideline_max=300,
                unit="ppm",
            ))
        if wq_model.ph_score is not None:
            param_scores.append(ParameterScore(
                parameter="ph",
                value=None,
                score=wq_model.ph_score,
                guideline_min=6.5,
                guideline_max=8.5,
                unit="",
            ))
        if wq_model.turbidity_score is not None:
            param_scores.append(ParameterScore(
                parameter="turbidity",
                value=None,
                score=wq_model.turbidity_score,
                guideline_min=0,
                guideline_max=1,
                unit="NTU",
            ))
        if wq_model.temp_score is not None:
            param_scores.append(ParameterScore(
                parameter="temperature",
                value=None,
                score=wq_model.temp_score,
                guideline_min=10,
                guideline_max=25,
                unit="°C",
            ))
        if wq_model.conductivity_score is not None:
            param_scores.append(ParameterScore(
                parameter="conductivity",
                value=None,
                score=wq_model.conductivity_score,
                guideline_min=0,
                guideline_max=500,
                unit="µS/cm",
            ))
        
        # Parse trends
        trends = {}
        if wq_model.trends:
            for param, trend_data in wq_model.trends.items():
                if trend_data:
                    trends[param] = TrendAnalysis(
                        parameter=param,
                        window=trend_data.get('window', '24h'),
                        direction=trend_data.get('direction', 'stable'),
                        magnitude=trend_data.get('magnitude', 0),
                        points=[TrendPoint(**p) for p in trend_data.get('points', [])],
                        slope_per_hour=trend_data.get('slope_per_hour', 0),
                    )
        
        # Parse anomaly flags
        anomaly_flags = {}
        if wq_model.anomaly_flags:
            for flag in wq_model.anomaly_flags:
                anomaly_flags[flag.get('parameter', '')] = flag.get('score', 0)
        
        water_quality = AquaScoreResponse(
            device_id=wq_model.device_id,
            timestamp=wq_model.timestamp,
            aquascore=wq_model.aquascore,
            parameter_scores=param_scores,
            trends=trends,
            anomaly_score=wq_model.anomaly_score,
            anomaly_flags=anomaly_flags,
            data_freshness_seconds=data_freshness_seconds,
            provenance="CALCULATED",
        )
    
    # Get filter health
    filter_health = None
    fh_result = await db.execute(
        select(FilterHealthModel)
        .where(FilterHealthModel.device_id == device_id)
        .order_by(desc(FilterHealthModel.timestamp))
        .limit(1)
    )
    fh_model = fh_result.scalar_one_or_none()
    if fh_model:
        filter_health = FilterHealthResponse(
            device_id=fh_model.device_id,
            timestamp=fh_model.timestamp,
            fsi=fh_model.fsi,
            fhi=fh_model.fhi,
            rul_days=fh_model.rul_days,
            rul_confidence_lower=fh_model.rul_confidence_lower,
            rul_confidence_upper=fh_model.rul_confidence_upper,
            model_name=fh_model.model_name,
            model_version=fh_model.model_version,
            dataset_version=fh_model.dataset_version,
            input_features=fh_model.input_features,
            explanation=fh_model.explanation,
            maintenance_band=fh_model.maintenance_band,
            confidence_level=fh_model.confidence_level,
        )
    
    # Get diagnostics
    diagnostics = None
    diag_result = await db.execute(
        select(DiagnosticsModel)
        .where(DiagnosticsModel.device_id == device_id)
        .order_by(desc(DiagnosticsModel.timestamp))
        .limit(1)
    )
    diag_model = diag_result.scalar_one_or_none()
    if diag_model:
        diagnostics = DiagnosticsDataResponse(
            device_id=diag_model.device_id,
            timestamp=diag_model.timestamp,
            pressure=diag_model.pressure_kpa,
            flow=diag_model.flow_lpm,
            leak=diag_model.leak_detected,
            tank=diag_model.tank_level_percent,
            pump=diag_model.pump_current_a,
        )
    
    # Get purification
    purification = None
    pp_result = await db.execute(
        select(PPModel)
        .where(PPModel.device_id == device_id)
        .order_by(desc(PPModel.timestamp))
        .limit(1)
    )
    pp_model = pp_result.scalar_one_or_none()
    if pp_model:
        purification = PurificationPerformanceResponse(
            device_id=pp_model.device_id,
            timestamp=pp_model.timestamp,
            rejection_rate=pp_model.rejection_rate,
            recovery_ratio=pp_model.recovery_ratio,
            permeate_quality=pp_model.permeate_quality,
            feed_quality=pp_model.feed_quality,
            efficiency=pp_model.efficiency,
        )
    
    # Get active alert
    active_alert = None
    alert_result = await db.execute(
        select(AlertModel)
        .where(
            and_(
                AlertModel.device_id == device_id,
                AlertModel.status.in_([AlertStatusModel.DETECTED, AlertStatusModel.OPEN, AlertStatusModel.ACKNOWLEDGED, AlertStatusModel.SNOOZED])
            )
        )
        .order_by(desc(AlertModel.created_at))
        .limit(1)
    )
    alert_model = alert_result.scalar_one_or_none()
    if alert_model:
        active_alert = AlertResponse(
            id=alert_model.id,
            device_id=alert_model.device_id,
            alert_code=alert_model.alert_code,
            severity=AlertSeveritySchema(alert_model.severity.value),
            status=AlertStatusSchema(alert_model.status.value),
            title=alert_model.title,
            message=alert_model.message,
            trigger_source=alert_model.trigger_source,
            trigger_value=alert_model.trigger_value,
            threshold_value=alert_model.threshold_value,
            evidence=alert_model.evidence or {},
            created_at=alert_model.created_at,
            acknowledged_at=alert_model.acknowledged_at,
            snoozed_until=alert_model.snoozed_until,
            resolved_at=alert_model.resolved_at,
            auto_cleared_at=alert_model.auto_cleared_at,
            created_by=alert_model.created_by,
            acknowledged_by=alert_model.acknowledged_by,
            resolved_by=alert_model.resolved_by,
        )
    
    # Calculate data freshness
    data_freshness_seconds = 0
    latest_telemetry = await get_latest_telemetry(device_id, db, device_claims)
    
    latest_telemetry_response = None
    if latest_telemetry:
        latest_telemetry_response = SensorReadingResponse(
            id=latest_telemetry.id,
            device_id=latest_telemetry.device_id,
            timestamp=latest_telemetry.timestamp,
            ingestion_timestamp=latest_telemetry.received_at,
            sequence=latest_telemetry.sequence,
            tds=latest_telemetry.tds,
            conductivity=latest_telemetry.ec,
            ph=latest_telemetry.ph,
            turbidity=latest_telemetry.turbidity,
            temperature=latest_telemetry.temperature,
            flow_rate=latest_telemetry.flow,
            inlet_pressure=latest_telemetry.pressure,
            outlet_pressure=latest_telemetry.outlet_pressure,
            tank_level=latest_telemetry.tank_level,
            leak=latest_telemetry.leak_detected,
            pump_current=latest_telemetry.pump_current,
            pump_power=latest_telemetry.pump_power,
            uv_state=latest_telemetry.uv_state,
            quality=QualityFlags(**latest_telemetry.quality_flags) if latest_telemetry.quality_flags else QualityFlags(),
            overall_quality=latest_telemetry.overall_quality,
            provenance="SIMULATED",
        )
        
        if latest_telemetry.ingestion_timestamp:
            data_freshness_seconds = int((datetime.utcnow() - latest_telemetry.ingestion_timestamp).total_seconds())
        else:
            data_freshness_seconds = 0
    else:
        data_freshness_seconds = 0
    
    # Get device response
    device_response = DeviceResponse(
        id=device.id,
        serial_number=device.serial_number,
        display_name=device.display_name,
        model=device.model,
        firmware_version=device.firmware_version,
        sensor_config=DeviceSensorConfig(**device.sensor_config) if device.sensor_config else DeviceSensorConfig(),
        safety_config=SafetyConfig(**device.safety_config) if device.safety_config else SafetyConfig(),
        status=DeviceStatus(device.status),
        last_seen=device.last_seen,
        created_at=device.created_at,
        updated_at=device.updated_at,
    )
    
    return DashboardData(
        device=device_response,
        latest_telemetry=latest_telemetry_response,
        water_quality=water_quality,
        filter_health=filter_health,
        diagnostics=diagnostics,
        purification=purification,
        active_alert=active_alert,
        data_freshness_seconds=data_freshness_seconds,
    )


@router.get("/{device_id}/dashboard", response_model=DashboardData)
async def get_dashboard(
    device_id: UUID,
    db: AsyncSession = Depends(get_db),
    device_claims = Depends(get_device_claims)
):
    """Get composite dashboard data for a device."""
    # Verify device exists and user has access
    device = await db.get(DeviceModel, device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    # Get latest telemetry
    latest_telemetry = await get_latest_telemetry(device_id, db, device_claims)
    
    # Get water quality
    water_quality = None
    wq_result = await db.execute(
        select(WaterQualityScoreModel)
        .where(WaterQualityScoreModel.device_id == device_id)
        .order_by(desc(WaterQualityScoreModel.timestamp))
        .limit(1)
    )
    wq_model = wq_result.scalar_one_or_none()
    if wq_model:
        # Parse parameter scores
        param_scores = []
        if wq_model.tds_score is not None:
            param_scores.append(ParameterScore(
                parameter="tds",
                value=None,
                score=wq_model.tds_score,
                guideline_min=0,
                guideline_max=300,
                unit="ppm",
            ))
        if wq_model.ph_score is not None:
            param_scores.append(ParameterScore(
                parameter="ph",
                value=None,
                score=wq_model.ph_score,
                guideline_min=6.5,
                guideline_max=8.5,
                unit="",
            ))
        if wq_model.turbidity_score is not None:
            param_scores.append(ParameterScore(
                parameter="turbidity",
                value=None,
                score=wq_model.turbidity_score,
                guideline_min=0,
                guideline_max=1,
                unit="NTU",
            ))
        if wq_model.temp_score is not None:
            param_scores.append(ParameterScore(
                parameter="temperature",
                value=None,
                score=wq_model.temp_score,
                guideline_min=10,
                guideline_max=25,
                unit="°C",
            ))
        if wq_model.conductivity_score is not None:
            param_scores.append(ParameterScore(
                parameter="conductivity",
                value=None,
                score=wq_model.conductivity_score,
                guideline_min=0,
                guideline_max=500,
                unit="µS/cm",
            ))
        
        # Parse trends
        trends = {}
        if wq_model.trends:
            for param, trend_data in wq_model.trends.items():
                if trend_data:
                    trends[param] = TrendAnalysis(
                        parameter=param,
                        window=trend_data.get('window', '24h'),
                        direction=trend_data.get('direction', 'stable'),
                        magnitude=trend_data.get('magnitude', 0),
                        points=[TrendPoint(**p) for p in trend_data.get('points', [])],
                        slope_per_hour=trend_data.get('slope_per_hour', 0),
                    )
        
        # Parse anomaly flags
        anomaly_flags = {}
        if wq_model.anomaly_flags:
            for flag in wq_model.anomaly_flags:
                anomaly_flags[flag.get('parameter', '')] = flag.get('score', 0)
        
        water_quality = AquaScoreResponse(
            device_id=wq_model.device_id,
            timestamp=wq_model.timestamp,
            aquascore=wq_model.aquascore,
            parameter_scores=param_scores,
            trends=trends,
            anomaly_score=wq_model.anomaly_score,
            anomaly_flags=anomaly_flags,
            data_freshness_seconds=data_freshness_seconds,
            provenance="CALCULATED",
        )
    
    # Get filter health
    filter_health = None
    fh_result = await db.execute(
        select(FilterHealthModel)
        .where(FilterHealthModel.device_id == device_id)
        .order_by(desc(FilterHealthModel.timestamp))
        .limit(1)
    )
    fh_model = fh_result.scalar_one_or_none()
    if fh_model:
        filter_health = FilterHealthResponse(
            device_id=fh_model.device_id,
            timestamp=fh_model.timestamp,
            fsi=fh_model.fsi,
            fhi=fh_model.fhi,
            rul_days=fh_model.rul_days,
            rul_confidence_lower=fh_model.rul_confidence_lower,
            rul_confidence_upper=fh_model.rul_confidence_upper,
            model_name=fh_model.model_name,
            model_version=fh_model.model_version,
            dataset_version=fh_model.dataset_version,
            input_features=fh_model.input_features,
            explanation=fh_model.explanation,
            maintenance_band=fh_model.maintenance_band,
            confidence_level=fh_model.confidence_level,
        )
    
    # Get diagnostics
    diagnostics = None
    diag_result = await db.execute(
        select(DiagnosticsModel)
        .where(DiagnosticsModel.device_id == device_id)
        .order_by(desc(DiagnosticsModel.timestamp))
        .limit(1)
    )
    diag_model = diag_result.scalar_one_or_none()
    if diag_model:
        diagnostics = DiagnosticsDataResponse(
            device_id=diag_model.device_id,
            timestamp=diag_model.timestamp,
            pressure=diag_model.pressure_kpa,
            flow=diag_model.flow_lpm,
            leak=diag_model.leak_detected,
            tank=diag_model.tank_level_percent,
            pump=diag_model.pump_current_a,
        )
    
    # Get purification
    purification = None
    pp_result = await db.execute(
        select(PPModel)
        .where(PPModel.device_id == device_id)
        .order_by(desc(PPModel.timestamp))
        .limit(1)
    )
    pp_model = pp_result.scalar_one_or_none()
    if pp_model:
        purification = PurificationPerformanceResponse(
            device_id=pp_model.device_id,
            timestamp=pp_model.timestamp,
            rejection_rate=pp_model.rejection_rate,
            recovery_ratio=pp_model.recovery_ratio,
            permeate_quality=pp_model.permeate_quality,
            feed_quality=pp_model.feed_quality,
            efficiency=pp_model.efficiency,
        )
    
    # Get active alert
    active_alert = None
    alert_result = await db.execute(
        select(AlertModel)
        .where(
            and_(
                AlertModel.device_id == device_id,
                AlertModel.status.in_([AlertStatusModel.DETECTED, AlertStatusModel.OPEN, AlertStatusModel.ACKNOWLEDGED, AlertStatusModel.SNOOZED])
            )
        )
        .order_by(desc(AlertModel.created_at))
        .limit(1)
    )
    alert_model = alert_result.scalar_one_or_none()
    if alert_model:
        active_alert = AlertResponse(
            id=alert_model.id,
            device_id=alert_model.device_id,
            alert_code=alert_model.alert_code,
            severity=AlertSeveritySchema(alert_model.severity.value),
            status=AlertStatusSchema(alert_model.status.value),
            title=alert_model.title,
            message=alert_model.message,
            trigger_source=alert_model.trigger_source,
            trigger_value=alert_model.trigger_value,
            threshold_value=alert_model.threshold_value,
            evidence=alert_model.evidence or {},
            created_at=alert_model.created_at,
            acknowledged_at=alert_model.acknowledged_at,
            snoozed_until=alert_model.snoozed_until,
            resolved_at=alert_model.resolved_at,
            auto_cleared_at=alert_model.auto_cleared_at,
            created_by=alert_model.created_by,
            acknowledged_by=alert_model.acknowledged_by,
            resolved_by=alert_model.resolved_by,
        )
    
    # Calculate data freshness
    data_freshness_seconds = 0
    latest_telemetry = await get_latest_telemetry(device_id, db, device_claims)
    
    latest_telemetry_response = None
    if latest_telemetry:
        latest_telemetry_response = SensorReadingResponse(
            id=latest_telemetry.id,
            device_id=latest_telemetry.device_id,
            timestamp=latest_telemetry.timestamp,
            ingestion_timestamp=latest_telemetry.received_at,
            sequence=latest_telemetry.sequence,
            tds=latest_telemetry.tds,
            conductivity=latest_telemetry.ec,
            ph=latest_telemetry.ph,
            turbidity=latest_telemetry.turbidity,
            temperature=latest_telemetry.temperature,
            flow_rate=latest_telemetry.flow,
            inlet_pressure=latest_telemetry.pressure,
            outlet_pressure=latest_telemetry.outlet_pressure,
            tank_level=latest_telemetry.tank_level,
            leak=latest_telemetry.leak_detected,
            pump_current=latest_telemetry.pump_current,
            pump_power=latest_telemetry.pump_power,
            uv_state=latest_telemetry.uv_state,
            quality=QualityFlags(**latest_telemetry.quality_flags) if latest_telemetry.quality_flags else QualityFlags(),
            overall_quality=latest_telemetry.overall_quality,
            provenance="SIMULATED",
        )
        
        if latest_telemetry.ingestion_timestamp:
            data_freshness_seconds = int((datetime.utcnow() - latest_telemetry.ingestion_timestamp).total_seconds())
        else:
            data_freshness_seconds = 0
    else:
        data_freshness_seconds = 0
    
    # Get device response
    device_response = DeviceResponse(
        id=device.id,
        serial_number=device.serial_number,
        display_name=device.display_name,
        model=device.model,
        firmware_version=device.firmware_version,
        sensor_config=DeviceSensorConfig(**device.sensor_config) if device.sensor_config else DeviceSensorConfig(),
        safety_config=SafetyConfig(**device.safety_config) if device.safety_config else SafetyConfig(),
        status=DeviceStatus(device.status),
        last_seen=device.last_seen,
        created_at=device.created_at,
        updated_at=device.updated_at,
    )
    
    return DashboardData(
        device=device_response,
        latest_telemetry=latest_telemetry_response,
        water_quality=water_quality,
        filter_health=filter_health,
        diagnostics=diagnostics,
        purification=purification,
        active_alert=active_alert,
        data_freshness_seconds=data_freshness_seconds,
    )