# AquaNexis — Backend Schema Reference

## 1. Pydantic Schemas (Request/Response)

### 1.1 Telemetry Schemas
```python
# schemas/telemetry.py
from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import Optional, Literal
from uuid import UUID

class SensorReadingInput(BaseModel):
    tds: Optional[float] = Field(None, ge=0, le=5000)
    ec: Optional[float] = Field(None, ge=0, le=8000)
    ph: Optional[float] = Field(None, ge=0, le=14)
    turbidity: Optional[float] = Field(None, ge=0, le=1000)
    temperature: Optional[float] = Field(None, ge=-10, le=60)
    flow: Optional[float] = Field(None, ge=0, le=100)
    pressure: Optional[float] = Field(None, ge=0, le=1000)
    tank_level: Optional[float] = Field(None, ge=0, le=100)
    leak_detected: Optional[bool] = None
    pump_current: Optional[float] = Field(None, ge=0, le=10)
    permeate_flow: Optional[float] = Field(None, ge=0, le=100)
    reject_flow: Optional[float] = Field(None, ge=0, le=100)
    uv_state: Optional[bool] = None
    vibration: Optional[float] = Field(None, ge=0, le=10)

class TelemetryIngestRequest(BaseModel):
    device_id: UUID
    timestamp: datetime
    readings: SensorReadingInput

class QualityFlag(BaseModel):
    range: Literal["OK", "SUSPECT", "BAD"]
    rate: Literal["OK", "SUSPECT", "BAD"]
    cross_sensor: Literal["OK", "SUSPECT", "BAD"]
    stuck: Literal["OK", "SUSPECT", "BAD"]

class QualityAssessment(BaseModel):
    overall: Literal["GOOD", "SUSPECT", "BAD"]
    flags: dict[str, QualityFlag]

class DerivedValues(BaseModel):
    aquascore: Optional[int] = Field(None, ge=0, le=100)
    fsi: Optional[float] = Field(None, ge=0, le=100)
    fhi: Optional[float] = Field(None, ge=0, le=100)
    rul_days: Optional[float] = Field(None, ge=0)

class TelemetryIngestResponse(BaseModel):
    accepted: bool
    reading_id: UUID
    quality_assessment: QualityAssessment
    derived: DerivedValues
```

### 1.2 Device Schemas
```python
# schemas/device.py
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from uuid import UUID
from datetime import datetime

class SensorConfig(BaseModel):
    enabled: bool = True
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    rate_limit: Optional[float] = None  # max change per minute
    calibration_offset: float = 0.0
    calibration_slope: float = 1.0

class DeviceSensorConfig(BaseModel):
    tds: SensorConfig = SensorConfig()
    ec: SensorConfig = SensorConfig()
    ph: SensorConfig = SensorConfig()
    turbidity: SensorConfig = SensorConfig()
    temperature: SensorConfig = SensorConfig()
    flow: SensorConfig = SensorConfig()
    pressure: SensorConfig = SensorConfig()
    tank_level: SensorConfig = SensorConfig()
    leak: SensorConfig = SensorConfig()
    pump_current: SensorConfig = SensorConfig()

class SafetyConfig(BaseModel):
    leak_action: Literal["close_inlet_valve", "stop_pump", "both"] = "close_inlet_valve"
    leak_validate_with: list[str] = ["flow_delta", "pressure_drop"]
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
    name: Optional[str] = Field(None, max_length=128)
    sensor_config: DeviceSensorConfig = DeviceSensorConfig()
    safety_config: SafetyConfig = SafetyConfig()

class DeviceUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=128)
    sensor_config: Optional[DeviceSensorConfig] = None
    safety_config: Optional[SafetyConfig] = None
    firmware_version: Optional[str] = Field(None, max_length=32)

class DeviceResponse(BaseModel):
    id: UUID
    serial_number: str
    name: Optional[str]
    firmware_version: Optional[str]
    sensor_config: DeviceSensorConfig
    calibration: Dict[str, Any]
    safety_config: SafetyConfig
    status: Literal["online", "offline", "error", "maintenance"]
    last_seen: Optional[datetime]
    created_at: datetime
    updated_at: datetime
```

### 1.3 Water Quality Schemas
```python
# schemas/water_quality.py
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID

class ParameterScore(BaseModel):
    parameter: str
    value: float
    score: int = Field(..., ge=0, le=100)
    guideline_min: Optional[float] = None
    guideline_max: Optional[float] = None
    unit: str

class TrendPoint(BaseModel):
    timestamp: datetime
    value: float

class TrendAnalysis(BaseModel):
    window: str  # "1h", "24h", "7d", "30d"
    direction: Literal["improving", "stable", "degrading"]
    magnitude: float  # % change
    points: List[TrendPoint]

class AnomalyFlag(BaseModel):
    parameter: str
    score: float
    threshold: float
    type: Literal["zscore", "iqr", "isolation_forest", "rate_of_change"]

class WaterQualityResponse(BaseModel):
    device_id: UUID
    timestamp: datetime
    aquascore: int = Field(..., ge=0, le=100)
    parameter_scores: List[ParameterScore]
    trends: List[TrendAnalysis]
    anomaly_score: float
    anomaly_flags: List[AnomalyFlag]
    data_freshness_seconds: int
```

### 1.4 Filter Health Schemas
```python
# schemas/filter_health.py
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
from uuid import UUID

class ModelMetadata(BaseModel):
    name: str
    version: str
    dataset_version: Optional[str] = None
    trained_at: Optional[datetime] = None
    metrics: Dict[str, float] = {}

class ExplanationPayload(BaseModel):
    top_factors: list[Dict[str, Any]]  # [{"feature": "pressure", "contribution": 0.35, "direction": "increasing"}]
    method: str  # "shap", "coefficients", "permutation"

class FilterHealthResponse(BaseModel):
    device_id: UUID
    timestamp: datetime
    fsi: float = Field(..., ge=0, le=100)  # Filter Stress Index
    fhi: float = Field(..., ge=0, le=100)  # Filter Health Index
    rul_days: Optional[float] = Field(None, ge=0)
    rul_confidence_lower: Optional[float] = None
    rul_confidence_upper: Optional[float] = None
    model_metadata: ModelMetadata
    input_features: Dict[str, float]
    explanation: Optional[ExplanationPayload] = None
    data_freshness_seconds: int
```

### 1.5 Diagnostics Schemas
```python
# schemas/diagnostics.py
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from uuid import UUID

class PressureDiagnostics(BaseModel):
    current_kpa: float
    trend_1h: float
    trend_24h: float
    fouling_indicator: float  # 0-1, higher = more fouling
    pump_curve_deviation: float  # % deviation from expected
    status: Literal["normal", "elevated", "critical"]

class FlowDiagnostics(BaseModel):
    current_lpm: float
    trend_1h: float
    trend_24h: float
    recovery_ratio: Optional[float] = None
    permeate_flow: Optional[float] = None
    reject_flow: Optional[float] = None
    status: Literal["normal", "low", "high", "unstable"]

class LeakDiagnostics(BaseModel):
    leak_detected: bool
    leak_probability: float  # 0-1
    flow_delta_lpm: float
    pressure_drop_kpa: float
    sensor_state: bool
    status: Literal["dry", "suspect", "leak_confirmed"]

class TankDiagnostics(BaseModel):
    level_percent: float
    fill_rate_lpm: Optional[float] = None
    empty_rate_lpm: Optional[float] = None
    stagnation_hours: float
    status: Literal["normal", "filling", "draining", "stagnant", "empty"]

class PumpDiagnostics(BaseModel):
    current_a: float
    power_w: Optional[float] = None
    efficiency_trend: float  # % change over 7d
    runtime_hours: float
    starts_count: int
    status: Literal["normal", "degraded", "overcurrent", "offline"]

class DiagnosticsResponse(BaseModel):
    device_id: UUID
    timestamp: datetime
    pressure: PressureDiagnostics
    flow: FlowDiagnostics
    leak: LeakDiagnostics
    tank: TankDiagnostics
    pump: PumpDiagnostics
    overall_status: Literal["healthy", "degraded", "critical"]
    data_freshness_seconds: int
```

### 1.6 Alert Schemas
```python
# schemas/alert.py
from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime
from uuid import UUID

class AlertBase(BaseModel):
    device_id: UUID
    alert_type: str
    severity: Literal["INFO", "WARNING", "CRITICAL"]
    trigger_source: str
    dedupe_key: str
    trigger_value: Optional[float] = None
    threshold_value: Optional[float] = None
    explanation: Optional[dict] = None

class AlertCreate(AlertBase):
    pass

class AlertUpdate(BaseModel):
    state: Optional[Literal["ACTIVE", "ACKNOWLEDGED", "RESOLVED"]] = None
    acknowledged_by: Optional[str] = None
    resolved_by: Optional[str] = None
    resolved_reason: Optional[str] = None

class AlertResponse(BaseModel):
    id: UUID
    device_id: UUID
    alert_type: str
    severity: Literal["INFO", "WARNING", "CRITICAL"]
    trigger_source: str
    dedupe_key: str
    trigger_value: Optional[float]
    threshold_value: Optional[float]
    explanation: Optional[dict]
    state: Literal["ACTIVE", "ACKNOWLEDGED", "RESOLVED"]
    created_at: datetime
    acknowledged_at: Optional[datetime]
    acknowledged_by: Optional[str]
    resolved_at: Optional[datetime]
    resolved_by: Optional[str]
    resolved_reason: Optional[str]

class AlertListQuery(BaseModel):
    device_id: Optional[UUID] = None
    state: Optional[Literal["ACTIVE", "ACKNOWLEDGED", "RESOLVED", "ALL"]] = "ACTIVE"
    severity: Optional[Literal["INFO", "WARNING", "CRITICAL"]] = None
    alert_type: Optional[str] = None
    limit: int = Field(50, ge=1, le=500)
    offset: int = Field(0, ge=0)
```

### 1.7 Maintenance Schemas
```python
# schemas/maintenance.py
from pydantic import BaseModel, Field
from typing import Optional, Literal, Dict, Any
from datetime import datetime
from uuid import UUID

class FilterReplacementRequest(BaseModel):
    device_id: UUID
    performed_by: str
    filter_type: str
    filter_serial: Optional[str] = None
    pre_metrics: Optional[Dict[str, float]] = None
    notes: Optional[str] = None

class CalibrationRequest(BaseModel):
    device_id: UUID
    performed_by: str
    sensor: Literal["tds", "ec", "ph", "turbidity", "temperature", "flow", "pressure", "tank_level"]
    reference_value: float
    measured_value: float
    notes: Optional[str] = None

class VerificationRequest(BaseModel):
    device_id: UUID
    performed_by: str
    maintenance_event_id: UUID
    post_metrics: Dict[str, float]
    passed: bool
    notes: Optional[str] = None

class MaintenanceEventResponse(BaseModel):
    id: UUID
    device_id: UUID
    event_type: Literal["FILTER_REPLACEMENT", "CALIBRATION", "VERIFICATION"]
    performed_at: datetime
    performed_by: str
    pre_metrics: Optional[Dict[str, float]]
    post_metrics: Optional[Dict[str, float]]
    notes: Optional[str]
    verified: bool
    verification_data: Optional[Dict[str, Any]]
```

### 1.8 Health/Readiness Schemas
```python
# schemas/health.py
from pydantic import BaseModel
from typing import Literal, Dict, Any

class HealthCheck(BaseModel):
    status: Literal["healthy", "degraded", "unhealthy"]
    service: str
    details: Dict[str, Any] = {}

class ReadinessCheck(BaseModel):
    ready: bool
    checks: Dict[str, HealthCheck]

class SystemReadinessResponse(BaseModel):
    device_connected: HealthCheck
    sensors_ready: HealthCheck
    calibration_status: HealthCheck
    data_freshness: HealthCheck
    backend_health: HealthCheck
    database_health: HealthCheck
    model_readiness: HealthCheck
    alert_readiness: HealthCheck
    safety_readiness: HealthCheck
    last_successful_test: HealthCheck
    overall_ready: bool
```

## 2. SQLAlchemy Models (Database)

### 2.1 Core Models
```python
# models/device.py
from sqlalchemy import Column, String, DateTime, JSON, Enum, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base
from datetime import datetime
import uuid
import enum

Base = declarative_base()

class DeviceStatus(str, enum.Enum):
    ONLINE = "online"
    OFFLINE = "offline"
    ERROR = "error"
    MAINTENANCE = "maintenance"

class Device(Base):
    __tablename__ = "devices"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    serial_number = Column(String(64), unique=True, nullable=False, index=True)
    name = Column(String(128), nullable=True)
    firmware_version = Column(String(32), nullable=True)
    sensor_config = Column(JSON, nullable=False, default=dict)
    calibration = Column(JSON, nullable=False, default=dict)
    safety_config = Column(JSON, nullable=False, default=dict)
    status = Column(Enum(DeviceStatus), nullable=False, default=DeviceStatus.OFFLINE)
    last_seen = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (Index("ix_devices_status_last_seen", "status", "last_seen"),)
```

```python
# models/reading.py
from sqlalchemy import Column, BigInteger, DateTime, Float, Boolean, JSON, String, Index, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime

Base = declarative_base()

class SensorReading(Base):
    __tablename__ = "sensor_readings"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    device_id = Column(UUID(as_uuid=True), ForeignKey("devices.id"), nullable=False, index=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    received_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    
    # Core Level-1 sensors
    tds = Column(Float, nullable=True)
    ec = Column(Float, nullable=True)
    ph = Column(Float, nullable=True)
    turbidity = Column(Float, nullable=True)
    temperature = Column(Float, nullable=True)
    flow = Column(Float, nullable=True)
    pressure = Column(Float, nullable=True)
    tank_level = Column(Float, nullable=True)
    leak_detected = Column(Boolean, nullable=True)
    pump_current = Column(Float, nullable=True)
    
    # Optional sensors
    permeate_flow = Column(Float, nullable=True)
    reject_flow = Column(Float, nullable=True)
    uv_state = Column(Boolean, nullable=True)
    vibration = Column(Float, nullable=True)
    
    # Quality assessment
    quality_flags = Column(JSON, nullable=False, default=dict)
    overall_quality = Column(String(16), nullable=False, default="GOOD")
    
    __table_args__ = (
        Index("ix_sensor_readings_device_timestamp", "device_id", "timestamp"),
        # TimescaleDB hypertable handled in migration
    )
```

```python
# models/water_quality.py
class WaterQualityScore(Base):
    __tablename__ = "water_quality_scores"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    device_id = Column(UUID(as_uuid=True), ForeignKey("devices.id"), nullable=False, index=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    
    aquascore = Column(Integer, nullable=False)  # 0-100
    tds_score = Column(Integer, nullable=True)
    ph_score = Column(Integer, nullable=True)
    turbidity_score = Column(Integer, nullable=True)
    temp_score = Column(Integer, nullable=True)
    
    trend_1h = Column(Float, nullable=True)
    trend_24h = Column(Float, nullable=True)
    trend_7d = Column(Float, nullable=True)
    
    anomaly_score = Column(Float, nullable=True)
    anomaly_flags = Column(JSON, nullable=False, default=dict)
    
    __table_args__ = (Index("ix_wqs_device_timestamp", "device_id", "timestamp"),)
```

```python
# models/filter_health.py
class FilterHealth(Base):
    __tablename__ = "filter_health"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    device_id = Column(UUID(as_uuid=True), ForeignKey("devices.id"), nullable=False, index=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    
    fsi = Column(Float, nullable=False)  # 0-100
    fhi = Column(Float, nullable=False)  # 0-100
    rul_days = Column(Float, nullable=True)
    rul_confidence_lower = Column(Float, nullable=True)
    rul_confidence_upper = Column(Float, nullable=True)
    
    model_name = Column(String(64), nullable=False)
    model_version = Column(String(32), nullable=False)
    dataset_version = Column(String(32), nullable=True)
    
    input_features = Column(JSON, nullable=False, default=dict)
    explanation = Column(JSON, nullable=True)
    
    __table_args__ = (Index("ix_fh_device_timestamp", "device_id", "timestamp"),)
```

```python
# models/alert.py
class AlertState(str, enum.Enum):
    ACTIVE = "ACTIVE"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    RESOLVED = "RESOLVED"

class AlertSeverity(str, enum.Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"

class Alert(Base):
    __tablename__ = "alerts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    device_id = Column(UUID(as_uuid=True), ForeignKey("devices.id"), nullable=False, index=True)
    alert_type = Column(String(64), nullable=False)
    severity = Column(Enum(AlertSeverity), nullable=False)
    trigger_source = Column(String(64), nullable=False)
    dedupe_key = Column(String(128), nullable=False)
    trigger_value = Column(Float, nullable=True)
    threshold_value = Column(Float, nullable=True)
    explanation = Column(JSON, nullable=True)
    state = Column(Enum(AlertState), nullable=False, default=AlertState.ACTIVE)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)
    acknowledged_by = Column(String(128), nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    resolved_by = Column(String(128), nullable=True)
    resolved_reason = Column(String(256), nullable=True)
    
    __table_args__ = (
        Index("ix_alerts_device_state", "device_id", "state"),
        Index("ix_alerts_created", "created_at"),
        UniqueConstraint("device_id", "dedupe_key", "state", 
                         name="uq_alert_dedupe_active",
                         postgresql_where=state.in_([AlertState.ACTIVE, AlertState.ACKNOWLEDGED])),
    )
```

```python
# models/maintenance.py
class MaintenanceEventType(str, enum.Enum):
    FILTER_REPLACEMENT = "FILTER_REPLACEMENT"
    CALIBRATION = "CALIBRATION"
    VERIFICATION = "VERIFICATION"

class MaintenanceEvent(Base):
    __tablename__ = "maintenance_events"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    device_id = Column(UUID(as_uuid=True), ForeignKey("devices.id"), nullable=False, index=True)
    event_type = Column(Enum(MaintenanceEventType), nullable=False)
    performed_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    performed_by = Column(String(128), nullable=False)
    pre_metrics = Column(JSON, nullable=True)
    post_metrics = Column(JSON, nullable=True)
    notes = Column(Text, nullable=True)
    verified = Column(Boolean, nullable=False, default=False)
    verification_data = Column(JSON, nullable=True)
    
    __table_args__ = (Index("ix_maint_device_performed", "device_id", "performed_at"),)
```

```python
# models/model_artifact.py
class ModelStatus(str, enum.Enum):
    STAGING = "staging"
    PRODUCTION = "production"
    ARCHIVED = "archived"

class ModelArtifact(Base):
    __tablename__ = "model_artifacts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(64), nullable=False)
    version = Column(String(32), nullable=False)
    dataset_version = Column(String(32), nullable=True)
    artifact_path = Column(String(512), nullable=False)
    metrics = Column(JSON, nullable=True)
    status = Column(Enum(ModelStatus), nullable=False, default=ModelStatus.STAGING)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    promoted_at = Column(DateTime(timezone=True), nullable=True)
    
    __table_args__ = (UniqueConstraint("name", "version", name="uq_model_name_version"),)
```

## 3. Alembic Migration Structure
```
alembic/
├── env.py
├── script.py.mako
└── versions/
    ├── 0001_initial_schema.py
    ├── 0002_add_timescale_hypertables.py
    ├── 0003_add_alert_dedupe_constraint.py
    └── 0004_add_model_artifacts.py
```

### 3.1 Initial Migration (0001_initial_schema.py)
```python
"""Initial schema"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '0001'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Devices
    op.create_table(
        'devices',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('serial_number', sa.String(64), nullable=False),
        sa.Column('name', sa.String(128), nullable=True),
        sa.Column('firmware_version', sa.String(32), nullable=True),
        sa.Column('sensor_config', postgresql.JSONB(), nullable=False, server_default='{}'),
        sa.Column('calibration', postgresql.JSONB(), nullable=False, server_default='{}'),
        sa.Column('safety_config', postgresql.JSONB(), nullable=False, server_default='{}'),
        sa.Column('status', sa.String(32), nullable=False, server_default='offline'),
        sa.Column('last_seen', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('serial_number'),
    )
    op.create_index('ix_devices_status_last_seen', 'devices', ['status', 'last_seen'])
    
    # Sensor Readings
    op.create_table(
        'sensor_readings',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('device_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('received_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('tds', sa.Float(), nullable=True),
        sa.Column('ec', sa.Float(), nullable=True),
        sa.Column('ph', sa.Float(), nullable=True),
        sa.Column('turbidity', sa.Float(), nullable=True),
        sa.Column('temperature', sa.Float(), nullable=True),
        sa.Column('flow', sa.Float(), nullable=True),
        sa.Column('pressure', sa.Float(), nullable=True),
        sa.Column('tank_level', sa.Float(), nullable=True),
        sa.Column('leak_detected', sa.Boolean(), nullable=True),
        sa.Column('pump_current', sa.Float(), nullable=True),
        sa.Column('permeate_flow', sa.Float(), nullable=True),
        sa.Column('reject_flow', sa.Float(), nullable=True),
        sa.Column('uv_state', sa.Boolean(), nullable=True),
        sa.Column('vibration', sa.Float(), nullable=True),
        sa.Column('quality_flags', postgresql.JSONB(), nullable=False, server_default='{}'),
        sa.Column('overall_quality', sa.String(16), nullable=False, server_default='GOOD'),
        sa.PrimaryKeyConstraint('device_id', 'timestamp', 'id'),
        sa.ForeignKeyConstraint(['device_id'], ['devices.id']),
    )
    op.create_index('ix_sensor_readings_device_timestamp', 'sensor_readings', ['device_id', 'timestamp'])
    
    # Water Quality Scores
    op.create_table(
        'water_quality_scores',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('device_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('aquascore', sa.SmallInteger(), nullable=False),
        sa.Column('tds_score', sa.SmallInteger(), nullable=True),
        sa.Column('ph_score', sa.SmallInteger(), nullable=True),
        sa.Column('turbidity_score', sa.SmallInteger(), nullable=True),
        sa.Column('temp_score', sa.SmallInteger(), nullable=True),
        sa.Column('trend_1h', sa.Float(), nullable=True),
        sa.Column('trend_24h', sa.Float(), nullable=True),
        sa.Column('trend_7d', sa.Float(), nullable=True),
        sa.Column('anomaly_score', sa.Float(), nullable=True),
        sa.Column('anomaly_flags', postgresql.JSONB(), nullable=False, server_default='{}'),
        sa.PrimaryKeyConstraint('device_id', 'timestamp', 'id'),
        sa.ForeignKeyConstraint(['device_id'], ['devices.id']),
    )
    op.create_index('ix_wqs_device_timestamp', 'water_quality_scores', ['device_id', 'timestamp'])
    
    # Filter Health
    op.create_table(
        'filter_health',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('device_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('fsi', sa.Float(), nullable=False),
        sa.Column('fhi', sa.Float(), nullable=False),
        sa.Column('rul_days', sa.Float(), nullable=True),
        sa.Column('rul_confidence_lower', sa.Float(), nullable=True),
        sa.Column('rul_confidence_upper', sa.Float(), nullable=True),
        sa.Column('model_name', sa.String(64), nullable=False),
        sa.Column('model_version', sa.String(32), nullable=False),
        sa.Column('dataset_version', sa.String(32), nullable=True),
        sa.Column('input_features', postgresql.JSONB(), nullable=False, server_default='{}'),
        sa.Column('explanation', postgresql.JSONB(), nullable=True),
        sa.PrimaryKeyConstraint('device_id', 'timestamp', 'id'),
        sa.ForeignKeyConstraint(['device_id'], ['devices.id']),
    )
    op.create_index('ix_fh_device_timestamp', 'filter_health', ['device_id', 'timestamp'])
    
    # ... (other tables similar)
    
    # Alerts
    op.create_table(
        'alerts',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('device_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('alert_type', sa.String(64), nullable=False),
        sa.Column('severity', sa.String(16), nullable=False),
        sa.Column('trigger_source', sa.String(64), nullable=False),
        sa.Column('dedupe_key', sa.String(128), nullable=False),
        sa.Column('trigger_value', sa.Float(), nullable=True),
        sa.Column('threshold_value', sa.Float(), nullable=True),
        sa.Column('explanation', postgresql.JSONB(), nullable=True),
        sa.Column('state', sa.String(16), nullable=False, server_default='ACTIVE'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('acknowledged_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('acknowledged_by', sa.String(128), nullable=True),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('resolved_by', sa.String(128), nullable=True),
        sa.Column('resolved_reason', sa.String(256), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['device_id'], ['devices.id']),
    )
    op.create_index('ix_alerts_device_state', 'alerts', ['device_id', 'state'])
    op.create_index('ix_alerts_created', 'alerts', ['created_at'])
    # Partial unique index for dedupe handled in separate migration

def downgrade():
    op.drop_table('alerts')
    op.drop_table('filter_health')
    op.drop_table('water_quality_scores')
    op.drop_table('sensor_readings')
    op.drop_table('devices')
```

### 3.2 TimescaleDB Migration (0002_add_timescale_hypertables.py)
```python
"""Add TimescaleDB hypertables"""
from alembic import op
import sqlalchemy as sa

revision = '0002'
down_revision = '0001'
branch_labels = None
depends_on = None

def upgrade():
    # Enable TimescaleDB extension
    op.execute("CREATE EXTENSION IF NOT EXISTS timescaledb;")
    
    # Convert to hypertables
    op.execute("""
        SELECT create_hypertable('sensor_readings', 'timestamp', 
            chunk_time_interval => INTERVAL '1 day',
            if_not_exists => TRUE);
    """)
    op.execute("""
        SELECT create_hypertable('water_quality_scores', 'timestamp', 
            chunk_time_interval => INTERVAL '1 day',
            if_not_exists => TRUE);
    """)
    op.execute("""
        SELECT create_hypertable('filter_health', 'timestamp', 
            chunk_time_interval => INTERVAL '1 day',
            if_not_exists => TRUE);
    """)
    op.execute("""
        SELECT create_hypertable('purification_performance', 'timestamp', 
            chunk_time_interval => INTERVAL '1 day',
            if_not_exists => TRUE);
    """)
    op.execute("""
        SELECT create_hypertable('system_diagnostics', 'timestamp', 
            chunk_time_interval => INTERVAL '1 day',
            if_not_exists => TRUE);
    """)
    
    # Add compression policies (optional, for older chunks)
    op.execute("""
        ALTER TABLE sensor_readings SET (
            timescaledb.compress,
            timescaledb.compress_segmentby = 'device_id'
        );
    """)
    op.execute("SELECT add_compression_policy('sensor_readings', INTERVAL '7 days');")

def downgrade():
    op.execute("DROP EXTENSION IF EXISTS timescaledb CASCADE;")
```

## 4. Database Indexes Summary

| Table | Index | Purpose |
|-------|-------|---------|
| devices | PK (id) | Primary lookup |
| devices | UQ (serial_number) | Provisioning lookup |
| devices | IX (status, last_seen) | Fleet dashboard |
| sensor_readings | PK (device_id, timestamp, id) | Time-series primary |
| sensor_readings | IX (device_id, timestamp) | Device history queries |
| water_quality_scores | PK (device_id, timestamp, id) | Time-series primary |
| water_quality_scores | IX (device_id, timestamp) | Dashboard trends |
| filter_health | PK (device_id, timestamp, id) | Time-series primary |
| filter_health | IX (device_id, timestamp) | RUL history |
| alerts | PK (id) | Alert lookup |
| alerts | IX (device_id, state) | Active alerts query |
| alerts | IX (created_at) | Alert history |
| alerts | UQ (device_id, dedupe_key, state) partial | Deduplication |
| maintenance_events | PK (id) | Event lookup |
| maintenance_events | IX (device_id, performed_at) | Maintenance history |
| model_artifacts | PK (id) | Model lookup |
| model_artifacts | UQ (name, version) | Registry integrity |