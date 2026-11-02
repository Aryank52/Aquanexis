"""
Pydantic schemas for telemetry API requests/responses.
"""
from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any, Literal
from uuid import UUID
from pydantic import BaseModel, Field, field_validator


# ===== Sensor Reading Schemas =====

class SensorReadingInput(BaseModel):
    """Input sensor values from device."""
    tds: Optional[float] = Field(None, ge=0, le=5000, description="Total Dissolved Solids (ppm)")
    conductivity: Optional[float] = Field(None, ge=0, le=10000, description="Electrical Conductivity (µS/cm)")
    ph: Optional[float] = Field(None, ge=0, le=14, description="pH (0-14)")
    turbidity: Optional[float] = Field(None, ge=0, le=1000, description="Turbidity (NTU)")
    temperature: Optional[float] = Field(None, ge=-20, le=80, description="Temperature (°C)")
    flow_rate: Optional[float] = Field(None, ge=0, le=100, description="Flow rate (L/min)")
    inlet_pressure: Optional[float] = Field(None, ge=0, le=2000, description="Inlet pressure (kPa)")
    outlet_pressure: Optional[float] = Field(None, ge=0, le=2000, description="Outlet pressure (kPa)")
    tank_level: Optional[float] = Field(None, ge=0, le=100, description="Tank level (%)")
    leak: Optional[bool] = Field(None, description="Leak detected")
    pump_current: Optional[float] = Field(None, ge=0, le=20, description="Pump current (A)")
    pump_power: Optional[float] = Field(None, ge=0, le=10000, description="Pump power (W)")
    uv_state: Optional[bool] = Field(None, description="UV lamp state")


class QualityFlag(BaseModel):
    """Quality flag for a single sensor."""
    state: Literal["valid", "suspect", "missing", "out_of_range", "calibration_due"] = "valid"
    message: Optional[str] = None
    expected_range: Optional[List[float]] = None
    actual_value: Optional[float] = None


class QualityFlags(BaseModel):
    """Quality flags for all sensors."""
    tds: QualityFlag = Field(default_factory=QualityFlag)
    conductivity: QualityFlag = Field(default_factory=QualityFlag)
    ph: QualityFlag = Field(default_factory=QualityFlag)
    turbidity: QualityFlag = Field(default_factory=QualityFlag)
    temperature: QualityFlag = Field(default_factory=QualityFlag)
    flow_rate: QualityFlag = Field(default_factory=QualityFlag)
    inlet_pressure: QualityFlag = Field(default_factory=QualityFlag)
    outlet_pressure: QualityFlag = Field(default_factory=QualityFlag)
    tank_level: QualityFlag = Field(default_factory=QualityFlag)
    leak: QualityFlag = Field(default_factory=QualityFlag)
    pump_current: QualityFlag = Field(default_factory=QualityFlag)
    pump_power: QualityFlag = Field(default_factory=QualityFlag)

    def overall(self) -> Literal["good", "suspect", "bad"]:
        states = [getattr(self, k).state for k in self.__fields__.keys()]
        if any(s == "out_of_range" for s in states):
            return "bad"
        if any(s in ("suspect", "calibration_due") for s in states):
            return "suspect"
        if all(s == "missing" for s in states):
            return "bad"
        return "good"


class TelemetryPayload(BaseModel):
    """Complete telemetry payload from device."""
    device_id: UUID
    timestamp: datetime
    sequence: Optional[int] = Field(None, ge=0, description="Sequence number for deduplication")
    firmware_version: Optional[str] = Field(None, max_length=32)
    readings: SensorReadingInput = Field(default_factory=SensorReadingInput)
    quality: Optional[QualityFlags] = None


class BatchTelemetryPayload(BaseModel):
    """Batch telemetry payload for buffered readings."""
    device_id: UUID
    firmware_version: Optional[str] = Field(None, max_length=32)
    readings: List[TelemetryPayload] = Field(default_factory=list, min_length=1, max_length=1000)


# ===== Device Schemas =====

class SensorConfig(BaseModel):
    enabled: bool = True
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    rate_limit: Optional[float] = None
    calibration_offset: float = 0.0
    calibration_slope: float = 1.0


class DeviceSensorConfig(BaseModel):
    tds: SensorConfig = Field(default_factory=SensorConfig)
    conductivity: SensorConfig = Field(default_factory=SensorConfig)
    ph: SensorConfig = Field(default_factory=SensorConfig)
    turbidity: SensorConfig = Field(default_factory=SensorConfig)
    temperature: SensorConfig = Field(default_factory=SensorConfig)
    flow_rate: SensorConfig = Field(default_factory=SensorConfig)
    inlet_pressure: SensorConfig = Field(default_factory=SensorConfig)
    outlet_pressure: SensorConfig = Field(default_factory=SensorConfig)
    tank_level: SensorConfig = Field(default_factory=SensorConfig)
    leak: SensorConfig = Field(default_factory=SensorConfig)
    pump_current: SensorConfig = Field(default_factory=SensorConfig)
    pump_power: SensorConfig = Field(default_factory=SensorConfig)


class SafetyConfig(BaseModel):
    """Safety configuration for device registration (minimal version).
    Full safety schemas are in app/schemas/safety.py
    """
    leak_action: Literal["close_inlet_valve", "stop_pump", "both"] = "close_inlet_valve"
    leak_validate_with: List[str] = Field(default_factory=lambda: ["flow_delta", "pressure_drop"])
    leak_cooldown_sec: int = 300
    pressure_max_kpa: float = 600.0
    pressure_action: Literal["open_relief", "stop_pump"] = "open_relief"
    pressure_cooldown_sec: int = 60
    flow_min_lpm: float = 0.1
    dry_run_action: Literal["stop_pump"] = "stop_pump"
    dry_run_cooldown_sec: int = 120
    pump_current_max_a: float = 2.5
    overcurrent_action: Literal["stop_pump"] = "stop_pump"
    overcurrent_cooldown_sec: int = 180


class DeviceCreate(BaseModel):
    serial_number: str = Field(..., min_length=1, max_length=64)
    display_name: Optional[str] = Field(None, max_length=128)
    model: Optional[str] = Field(None, max_length=64)
    firmware_version: Optional[str] = Field(None, max_length=32)
    sensor_config: DeviceSensorConfig = Field(default_factory=DeviceSensorConfig)
    safety_config: SafetyConfig = Field(default_factory=SafetyConfig)
    capabilities: Dict[str, Any] = Field(default_factory=dict)


class DeviceUpdate(BaseModel):
    display_name: Optional[str] = Field(None, max_length=128)
    model: Optional[str] = Field(None, max_length=64)
    firmware_version: Optional[str] = Field(None, max_length=32)
    sensor_config: Optional[DeviceSensorConfig] = None
    safety_config: Optional[SafetyConfig] = None
    capabilities: Optional[Dict[str, Any]] = None
    status: Optional[Literal["active", "offline", "degraded", "maintenance"]] = None


class DeviceResponse(BaseModel):
    id: UUID
    serial_number: str
    display_name: Optional[str]
    model: Optional[str]
    firmware_version: Optional[str]
    sensor_config: DeviceSensorConfig
    safety_config: SafetyConfig
    calibration: Dict[str, Any]
    status: Literal["active", "offline", "degraded", "maintenance"]
    last_seen_at: Optional[datetime]
    capabilities: Dict[str, Any]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ===== Telemetry Response Schemas =====

class TelemetryIngestResponse(BaseModel):
    """Response for telemetry ingestion."""
    accepted: bool
    reading_id: int
    quality: QualityFlags
    derived: Optional[Dict[str, Any]] = None


class BatchTelemetryResult(BaseModel):
    accepted: int = 0
    rejected: int = 0
    duplicates: int = 0
    invalid: int = 0
    errors: List[Dict[str, Any]] = Field(default_factory=list)


class SensorReadingResponse(BaseModel):
    """Stored sensor reading with quality."""
    id: int
    device_id: UUID
    timestamp: datetime
    ingestion_timestamp: datetime
    sequence: Optional[int]
    tds: Optional[float]
    conductivity: Optional[float]
    ph: Optional[float]
    turbidity: Optional[float]
    temperature: Optional[float]
    flow_rate: Optional[float]
    inlet_pressure: Optional[float]
    outlet_pressure: Optional[float]
    tank_level: Optional[float]
    leak: Optional[bool]
    pump_current: Optional[float]
    pump_power: Optional[float]
    uv_state: Optional[bool]
    quality: QualityFlags
    overall_quality: Literal["good", "suspect", "bad"]

    class Config:
        from_attributes = True


class TelemetryHistoryQuery(BaseModel):
    device_id: UUID
    start: datetime
    end: datetime
    interval: Optional[str] = "1m"  # 1m, 5m, 1h, 1d
    limit: int = Field(1000, ge=1, le=5000)
    sensors: Optional[List[str]] = None


class TelemetryHistoryResponse(BaseModel):
    device_id: UUID
    interval: str
    series: Dict[str, List[Dict[str, Any]]]


class DeviceStatusResponse(BaseModel):
    device_id: UUID
    status: Literal["active", "offline", "degraded", "maintenance"]
    last_seen_at: Optional[datetime]
    last_reading: Optional[SensorReadingResponse] = None
    sensor_health: Dict[str, Literal["valid", "suspect", "missing", "out_of_range", "calibration_due"]] = Field(default_factory=dict)


# ===== Water Quality Schemas =====

class ParameterScore(BaseModel):
    parameter: str
    value: Optional[float]
    score: int = Field(ge=0, le=100)
    guideline_min: Optional[float]
    guideline_max: Optional[float]
    unit: str
    status: Literal["ideal", "acceptable", "poor", "missing"]


class TrendPoint(BaseModel):
    timestamp: datetime
    value: float


class TrendAnalysis(BaseModel):
    parameter: str
    window: str
    direction: Literal["improving", "stable", "degrading"]
    magnitude: float
    points: List[TrendPoint]
    slope_per_hour: float


class AnomalyFlag(BaseModel):
    parameter: str
    score: float
    threshold: float
    type: Literal["zscore", "iqr", "rate_of_change", "isolation_forest"]
    message: str


class AquaScoreResponse(BaseModel):
    device_id: UUID
    timestamp: datetime
    overall_score: int = Field(ge=0, le=100)
    parameter_scores: List[ParameterScore]
    trends: List[TrendAnalysis]
    anomaly_score: float
    anomaly_flags: List[AnomalyFlag]
    data_freshness_seconds: int


# ===== Filter Health Schemas =====

class ModelMetadata(BaseModel):
    name: str
    version: str
    dataset_version: Optional[str] = None
    trained_at: Optional[datetime] = None
    metrics: Dict[str, float] = Field(default_factory=dict)


class ExplanationPayload(BaseModel):
    top_factors: List[Dict[str, Any]]
    method: str


class FilterHealthResponse(BaseModel):
    device_id: UUID
    timestamp: datetime
    fsi: float
    fhi: float
    rul_days: Optional[float] = None
    rul_confidence_lower: Optional[float] = None
    rul_confidence_upper: Optional[float] = None
    model_metadata: ModelMetadata
    input_features: Dict[str, float] = Field(default_factory=dict)
    explanation: Optional[ExplanationPayload] = None
    data_freshness_seconds: int


# ===== Alert Schemas =====

class AlertSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class AlertStatus(str, Enum):
    DETECTED = "detected"
    OPEN = "open"
    ACKNOWLEDGED = "acknowledged"
    SNOOZED = "snoozed"
    RESOLVED = "resolved"
    AUTO_CLEARED = "auto_cleared"


class DeviceStatus(str, Enum):
    ONLINE = "online"
    DEGRADED = "degraded"
    OFFLINE = "offline"
    MAINTENANCE = "maintenance"
    ERROR = "error"


class AlertBase(BaseModel):
    id: UUID
    device_id: UUID
    alert_code: str
    severity: AlertSeverity
    status: AlertStatus
    title: str
    message: str
    trigger_source: str
    trigger_value: Optional[Any] = None
    threshold_value: Optional[Any] = None
    evidence: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    acknowledged_at: Optional[datetime] = None
    snoozed_until: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    auto_cleared_at: Optional[datetime] = None
    created_by: Optional[str] = None
    acknowledged_by: Optional[str] = None
    resolved_by: Optional[str] = None

    class Config:
        from_attributes = True


class AlertResponse(AlertBase):
    pass


class AlertListQuery(BaseModel):
    device_id: Optional[UUID] = None
    alert_code: Optional[str] = None
    severity: Optional[AlertSeverity] = None
    status: Optional[AlertStatus] = None
    start: Optional[datetime] = None
    end: Optional[datetime] = None
    limit: int = Field(50, ge=1, le=200)
    offset: int = Field(0, ge=0)


class AlertAcknowledgeRequest(BaseModel):
    user: Optional[str] = None


class AlertSnoozeRequest(BaseModel):
    duration_minutes: int = Field(..., ge=1, le=1440)  # Max 24 hours
    user: Optional[str] = None


class AlertResolveRequest(BaseModel):
    user: Optional[str] = None


class AlertTransitionResponse(BaseModel):
    success: bool
    alert: AlertResponse
    message: Optional[str] = None


# ===== Phase E: Filter Intelligence Enhancement Schemas =====

class CounterfactualAnalysisResponse(BaseModel):
    device_id: UUID
    timestamp: datetime
    previous_rul_days: Optional[float] = None
    current_rul_days: Optional[float] = None
    rul_change_days: Optional[float] = None
    rul_change_pct: Optional[float] = None
    contributing_changes: List[Dict[str, Any]] = Field(default_factory=list)
    narrative: str


class MaintenanceBandResponse(BaseModel):
    band: str
    description: str
    threshold_score: int


class RULStabilityResponse(BaseModel):
    device_id: UUID
    window_hours: int
    readings_count: int
    rul_values: List[float]
    max_change_pct: float
    is_stable: bool
    instability_reason: Optional[str] = None


class BaselineMetricsResponse(BaseModel):
    device_id: UUID
    status: str
    needed_samples: Optional[int] = None
    flow_baseline_lpm: Optional[float] = None
    pressure_baseline_kpa: Optional[float] = None
    delta_pressure_baseline_kpa: Optional[float] = None
    turbidity_baseline_ntu: Optional[float] = None
    tds_baseline_ppm: Optional[float] = None
    daily_volume_baseline_l: Optional[float] = None
    pressure_stability_cv: Optional[float] = None
    flow_stability_cv: Optional[float] = None
    window_hours: int
    sample_count: int
    last_updated: str
    calculation_version: str


class ModelArtifactResponse(BaseModel):
    model_id: str
    model_type: str
    version: str
    dataset_version: str
    feature_schema_version: str
    training_timestamp: datetime
    validation_timestamp: Optional[datetime] = None
    metrics: Dict[str, float]
    status: str
    artifact_path: str
    notes: str = ""


class DatasetMetadataResponse(BaseModel):
    dataset_id: str
    dataset_type: str
    source: str
    date_range: List[str]
    schema_version: str
    created_at: datetime
    preprocessing_version: str
    record_count: int
    notes: str = ""


class ExperimentRecordResponse(BaseModel):
    experiment_id: str
    experiment_type: str
    filter_id: Optional[str] = None
    filter_condition: str
    water_condition: str
    start_time: datetime
    end_time: Optional[datetime] = None
    flow_lpm: Optional[float] = None
    pressure_kpa: Optional[float] = None
    temperature_c: Optional[float] = None
    turbidity_ntu: Optional[float] = None
    tds_ppm: Optional[float] = None
    duration_hours: Optional[float] = None
    volume_l: Optional[float] = None
    notes: str = ""
    recorded_by: str
    sensor_readings: List[Dict[str, Any]]
    annotations: List[Dict[str, Any]]
    tags: List[str]


# ===== Safety Schemas =====

class SafetyConfigResponse(BaseModel):
    device_id: UUID
    leak_action: str
    leak_validate_with: List[str]
    leak_cooldown_sec: int
    leak_persistence_readings: int
    pressure_max_kpa: float
    pressure_action: str
    pressure_cooldown_sec: int
    pressure_min_kpa: float
    pressure_action_low: str
    flow_min_lpm: float
    dry_run_action: str
    dry_run_cooldown_sec: int
    flow_unstable_threshold_pct: float
    pump_current_max_a: float
    overcurrent_action: str
    overcurrent_cooldown_sec: int
    pump_power_max_w: float
    persistence_required_readings: int
    cooldown_enabled: bool
    cooldown_by_code: Dict[str, int]


class SafetyConfigUpdate(BaseModel):
    leak_action: Optional[str] = None
    leak_validate_with: Optional[List[str]] = None
    leak_cooldown_sec: Optional[int] = None
    leak_persistence_readings: Optional[int] = None
    pressure_max_kpa: Optional[float] = None
    pressure_action: Optional[str] = None
    pressure_cooldown_sec: Optional[int] = None
    pressure_min_kpa: Optional[float] = None
    pressure_action_low: Optional[str] = None
    flow_min_lpm: Optional[float] = None
    dry_run_action: Optional[str] = None
    dry_run_cooldown_sec: Optional[int] = None
    flow_unstable_threshold_pct: Optional[float] = None
    pump_current_max_a: Optional[float] = None
    overcurrent_action: Optional[str] = None
    overcurrent_cooldown_sec: Optional[int] = None
    pump_power_max_w: Optional[float] = None
    persistence_required_readings: Optional[int] = None
    cooldown_enabled: Optional[bool] = None
    cooldown_by_code: Optional[Dict[str, int]] = None


class SafetyTestRequest(BaseModel):
    device_id: UUID
    test_type: Literal["leak", "pressure_high", "pressure_low", "flow_low", "pump_overcurrent", "dry_run"]
    custom_reading: Optional[Dict[str, Any]] = None


class SafetyTestResponse(BaseModel):
    test_type: str
    passed: bool
    details: Dict[str, Any]
    simulated_action: Optional[str] = None


class SafetyActionCommand(BaseModel):
    command_id: UUID
    device_id: UUID
    action_type: Literal["close_inlet_valve", "stop_pump", "open_relief_valve", "both_valve_and_pump"]
    event_type: str
    trigger_value: float
    threshold_value: float
    timestamp: datetime
    timeout_sec: int = 5
    signature: Optional[str] = None


class SafetyActionResponse(BaseModel):
    command_id: UUID
    device_id: UUID
    action_type: Literal["close_inlet_valve", "stop_pump", "open_relief_valve", "both_valve_and_pump"]
    status: Literal["pending", "executing", "completed", "failed", "validation_failed", "cooldown_active"]
    executed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    firmware_response: Optional[Dict[str, Any]] = None


# ===== Additional Response Models for Dashboard =====

class AquaScoreResponse(BaseModel):
    device_id: UUID
    timestamp: datetime
    aquascore: int
    parameter_scores: List[ParameterScore] = Field(default_factory=list)
    trends: Dict[str, TrendAnalysis] = Field(default_factory=dict)
    anomaly_score: Optional[float] = None
    anomaly_flags: Dict[str, float] = Field(default_factory=dict)


class DiagnosticsDataResponse(BaseModel):
    device_id: UUID
    timestamp: datetime
    pressure: Optional[float] = None
    flow: Optional[float] = None
    leak: Optional[bool] = None
    tank: Optional[float] = None
    pump: Optional[float] = None


class PurificationPerformanceResponse(BaseModel):
    device_id: UUID
    timestamp: datetime
    rejection_rate: Optional[float] = None
    recovery_ratio: Optional[float] = None
    permeate_quality: Optional[float] = None
    feed_quality: Optional[float] = None
    efficiency: Optional[float] = None


# Aliases for backward compatibility
WaterQualityResponse = AquaScoreResponse
# FilterHealthResponse uses the domain FilterHealthIndex model from app.domain.filter_intelligence
from app.domain.filter_intelligence import FilterHealthIndex
FilterHealthResponse = FilterHealthIndex
DiagnosticsDataResponse = DiagnosticsDataResponse
PurificationPerformanceResponse = PurificationPerformanceResponse


# ===== Dashboard Composite =====

class DashboardData(BaseModel):
    device: DeviceResponse
    latest_telemetry: Optional[SensorReadingResponse] = None
    water_quality: Optional[WaterQualityResponse] = None
    filter_health: Optional[FilterHealthResponse] = None
    diagnostics: Optional[DiagnosticsDataResponse] = None
    purification: Optional[PurificationPerformanceResponse] = None
    active_alert: Optional[AlertResponse] = None
    data_freshness_seconds: int


class SafetyConfigResponse(BaseModel):
    device_id: UUID
    leak_action: str
    leak_validate_with: List[str]
    leak_cooldown_sec: int
    leak_persistence_readings: int
    pressure_max_kpa: float
    pressure_action: str
    pressure_cooldown_sec: int
    pressure_min_kpa: float
    pressure_action_low: str
    flow_min_lpm: float
    dry_run_action: str
    dry_run_cooldown_sec: int
    flow_unstable_threshold_pct: float
    pump_current_max_a: float
    overcurrent_action: str
    overcurrent_cooldown_sec: int
    pump_power_max_w: float
    persistence_required_readings: int
    cooldown_enabled: bool
    cooldown_by_code: Dict[str, int]


class SafetyConfigUpdate(BaseModel):
    leak_action: Optional[str] = None
    leak_validate_with: Optional[List[str]] = None
    leak_cooldown_sec: Optional[int] = None
    leak_persistence_readings: Optional[int] = None
    pressure_max_kpa: Optional[float] = None
    pressure_action: Optional[str] = None
    pressure_cooldown_sec: Optional[int] = None
    pressure_min_kpa: Optional[float] = None
    pressure_action_low: Optional[str] = None
    flow_min_lpm: Optional[float] = None
    dry_run_action: Optional[str] = None
    dry_run_cooldown_sec: Optional[int] = None
    flow_unstable_threshold_pct: Optional[float] = None
    pump_current_max_a: Optional[float] = None
    overcurrent_action: Optional[str] = None
    overcurrent_cooldown_sec: Optional[int] = None
    pump_power_max_w: Optional[float] = None
    persistence_required_readings: Optional[int] = None
    cooldown_enabled: Optional[bool] = None
    cooldown_by_code: Optional[Dict[str, int]] = None


class SafetyTestRequest(BaseModel):
    device_id: UUID
    test_type: Literal["leak", "pressure_high", "pressure_low", "flow_low", "pump_overcurrent", "dry_run"]
    custom_reading: Optional[Dict[str, Any]] = None


class SafetyTestResponse(BaseModel):
    test_type: str
    passed: bool
    details: Dict[str, Any]
    simulated_action: Optional[str] = None


class SafetyActionCommand(BaseModel):
    command_id: UUID
    device_id: UUID
    action_type: Literal["close_inlet_valve", "stop_pump", "open_relief_valve", "both_valve_and_pump"]
    event_type: str
    trigger_value: float
    threshold_value: float
    timestamp: datetime
    timeout_sec: int = 5
    signature: Optional[str] = None


class SafetyActionResponse(BaseModel):
    command_id: UUID
    device_id: UUID
    action_type: Literal["close_inlet_valve", "stop_pump", "open_relief_valve", "both_valve_and_pump"]
    status: Literal["pending", "executing", "completed", "failed", "validation_failed", "cooldown_active"]
    executed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    firmware_response: Optional[Dict[str, Any]] = None


# ===== Additional Response Models for Dashboard =====

class AquaScoreResponse(BaseModel):
    device_id: UUID
    timestamp: datetime
    aquascore: int
    parameter_scores: List[ParameterScore] = Field(default_factory=list)
    trends: Dict[str, TrendAnalysis] = Field(default_factory=dict)
    anomaly_score: Optional[float] = None
    anomaly_flags: Dict[str, float] = Field(default_factory=dict)


class DiagnosticsDataResponse(BaseModel):
    device_id: UUID
    timestamp: datetime
    pressure: Optional[float] = None
    flow: Optional[float] = None
    leak: Optional[bool] = None
    tank: Optional[float] = None
    pump: Optional[float] = None


class PurificationPerformanceResponse(BaseModel):
    device_id: UUID
    timestamp: datetime
    rejection_rate: Optional[float] = None
    recovery_ratio: Optional[float] = None
    permeate_quality: Optional[float] = None
    feed_quality: Optional[float] = None
    efficiency: Optional[float] = None


# Aliases for backward compatibility
WaterQualityResponse = AquaScoreResponse
# FilterHealthResponse uses the domain FilterHealthIndex model from app.domain.filter_intelligence
from app.domain.filter_intelligence import FilterHealthIndex
FilterHealthResponse = FilterHealthIndex
DiagnosticsDataResponse = DiagnosticsDataResponse
PurificationPerformanceResponse = PurificationPerformanceResponse


# ===== Dashboard Composite =====

class DashboardData(BaseModel):
    device: DeviceResponse
    latest_telemetry: Optional[SensorReadingResponse] = None
    water_quality: Optional[WaterQualityResponse] = None
    filter_health: Optional[FilterHealthResponse] = None
    diagnostics: Optional[DiagnosticsDataResponse] = None
    purification: Optional[PurificationPerformanceResponse] = None
    active_alert: Optional[AlertResponse] = None
    data_freshness_seconds: int