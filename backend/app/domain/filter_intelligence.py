"""
Filter Intelligence domain - Filter Stress Index, Filter Health Index, RUL.
Pure Python, no framework dependencies.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID


class FilterStressState(str, Enum):
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"


class FilterHealthState(str, Enum):
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"
    CRITICAL = "critical"


class FailureRiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class PredictionStatus(str, Enum):
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    MODEL_MISSING = "model_missing"
    INSUFFICIENT_DATA = "insufficient_data"
    LOW_CONFIDENCE = "low_confidence"
    HIGH_CONFIDENCE = "high_confidence"
    MEDIUM_CONFIDENCE = "medium_confidence"


class MaintenanceBand(str, Enum):
    NORMAL = "normal"
    MONITOR = "monitor"
    PLAN_MAINTENANCE = "plan_maintenance"
    REPLACE_RECOMMENDED = "replace_recommended"


class DatasetType(str, Enum):
    SYNTHETIC = "synthetic"
    CONTROLLED_EXPERIMENT = "controlled_experiment"
    REAL_OPERATIONAL = "real_operational"


@dataclass
class FilterStressIndex:
    """Filter Stress Index - deterministic engineering index."""

    device_id: UUID
    timestamp: datetime
    state: FilterStressState  # LOW, MODERATE, HIGH
    score: float  # 0-100, higher = more stress
    contributors: List[str] = field(default_factory=list)
    evidence: Dict[str, Any] = field(default_factory=dict)
    calculation_version: str = "1.0"
    config_version: str = "1.0"
    # Raw component scores for transparency
    differential_pressure_score: Optional[float] = None
    flow_deviation_score: Optional[float] = None
    turbidity_exposure_score: Optional[float] = None
    cumulative_volume_score: Optional[float] = None
    filter_age_score: Optional[float] = None
    operating_hours_score: Optional[float] = None
    tds_trend_score: Optional[float] = None
    # Pressure differential as first-class feature
    pressure_differential_kpa: Optional[float] = None
    pressure_differential_baseline_kpa: Optional[float] = None
    pressure_differential_rate_of_change_kpa_per_hour: Optional[float] = None


@dataclass
class FilterHealthIndex:
    """Filter Health Index - 0-100 health score."""

    device_id: UUID
    timestamp: datetime
    health_score: int  # 0-100
    state: FilterHealthState
    confidence: float  # 0-1
    contributing_factors: List[str] = field(default_factory=list)
    evidence: Dict[str, Any] = field(default_factory=dict)
    calculation_version: str = "2.0"
    # Component breakdown
    stress_component: Optional[float] = None
    lifecycle_component: Optional[float] = None
    usage_component: Optional[float] = None
    pressure_flow_component: Optional[float] = None
    historical_behavior_component: Optional[float] = None
    # Maintenance band
    maintenance_band: Optional[str] = None
    # Counterfactual analysis
    counterfactual: Optional[Dict[str, Any]] = None


@dataclass
class RULPrediction:
    """Remaining Useful Life prediction."""

    device_id: UUID
    timestamp: datetime
    rul_days: Optional[float] = None
    confidence_lower: Optional[float] = None
    confidence_upper: Optional[float] = None
    status: PredictionStatus = PredictionStatus.UNAVAILABLE
    model_name: str = ""
    model_version: str = ""
    dataset_version: str = ""
    input_features: Dict[str, float] = field(default_factory=dict)
    explanation: Optional[Dict[str, Any]] = None
    feature_importance: Dict[str, float] = field(default_factory=dict)
    # Prediction stability
    previous_rul_days: Optional[float] = None
    rul_change_days: Optional[float] = None
    is_stable: bool = True
    # Confidence level
    confidence_level: str = "medium"
    counterfactual: Optional[Dict[str, Any]] = None


@dataclass
class FailureRiskAssessment:
    """Failure risk classification."""

    device_id: UUID
    timestamp: datetime
    risk_level: FailureRiskLevel
    risk_score: float  # 0-100
    confidence: float
    evidence: Dict[str, Any] = field(default_factory=dict)
    contributing_factors: List[str] = field(default_factory=list)
    calculation_version: str = "1.0"
    # Component scores
    rul_risk_component: Optional[float] = None
    filter_health_risk_component: Optional[float] = None
    stress_state_component: Optional[float] = None
    anomaly_evidence_component: Optional[float] = None
    maintenance_band: Optional[str] = None


@dataclass
class PurificationPerformance:
    """Purification performance metrics."""

    device_id: UUID
    timestamp: datetime
    rejection_rate: Optional[float] = None  # %
    recovery_ratio: Optional[float] = None  # %
    feed_tds: Optional[float] = None  # ppm
    permeate_tds: Optional[float] = None  # ppm
    feed_conductivity: Optional[float] = None  # µS/cm
    permeate_conductivity: Optional[float] = None  # µS/cm
    permeate_flow: Optional[float] = None  # L/min
    reject_flow: Optional[float] = None  # L/min
    feed_quality: Optional[float] = None
    permeate_quality: Optional[float] = None
    efficiency: Optional[float] = None
    calculation_version: str = "1.0"


@dataclass
class HydraulicIntelligence:
    """Hydraulic intelligence metrics."""

    device_id: UUID
    timestamp: datetime
    differential_pressure: Optional[float] = None  # kPa
    flow_deviation_pct: Optional[float] = None  # % from baseline
    fill_time_deviation_pct: Optional[float] = None  # % from baseline
    pressure_stability: Optional[float] = None  # volatility metric
    pressure_trend: Optional[float] = None  # kPa/hour
    flow_trend: Optional[float] = None  # L/min/hour
    inlet_pressure: Optional[float] = None
    outlet_pressure: Optional[float] = None
    flow_rate: Optional[float] = None
    calculation_version: str = "1.0"
    # Baseline tracking
    pressure_baseline_kpa: Optional[float] = None
    flow_baseline_lpm: Optional[float] = None
    baseline_window_hours: Optional[float] = None


@dataclass
class AquaScoreExplanation:
    """Explanation for AquaScore."""

    overall_score: int
    state: str  # EXCELLENT, GOOD, FAIR, POOR
    confidence: float
    contributors: List[Dict[str, Any]]  # parameter, value, score, weight, contribution
    excluded_signals: List[str]
    data_quality: str  # HIGH, MEDIUM, LOW
    calculation_version: str = "1.0"


# Configuration classes for tuning
@dataclass
class FilterStressConfig:
    """Configuration for Filter Stress Index calculation."""

    # Differential pressure thresholds (kPa)
    dp_low_threshold: float = 50.0
    dp_high_threshold: float = 200.0
    dp_weight: float = 0.25

    # Flow deviation thresholds (% from baseline)
    flow_dev_low_threshold: float = 5.0
    flow_dev_high_threshold: float = 20.0
    flow_dev_weight: float = 0.20

    # Turbidity exposure (NTU-hours)
    turbidity_exposure_low: float = 10.0
    turbidity_exposure_high: float = 100.0
    turbidity_weight: float = 0.15

    # Cumulative volume (L)
    cum_volume_low: float = 1000.0
    cum_volume_high: float = 10000.0
    cum_volume_weight: float = 0.15

    # Filter age (days)
    age_low: float = 90.0
    age_high: float = 365.0
    age_weight: float = 0.10

    # Operating hours
    op_hours_low: float = 500.0
    op_hours_high: float = 2000.0
    op_hours_weight: float = 0.08

    # TDS trend
    tds_trend_weight: float = 0.07


@dataclass
class FilterHealthConfig:
    """Configuration for Filter Health Index calculation."""

    stress_weight: float = 0.30
    lifecycle_weight: float = 0.25
    usage_weight: float = 0.20
    pressure_flow_weight: float = 0.15
    historical_behavior_weight: float = 0.10

    # State thresholds
    excellent_min: int = 90
    good_min: int = 70
    fair_min: int = 50
    poor_min: int = 30

    # Maintenance band thresholds
    monitor_min: int = 70
    plan_maintenance_min: int = 50
    replace_recommended_min: int = 30


@dataclass
class RULConfig:
    """Configuration for RUL prediction."""

    model_path: str = "/app/models/rul_model.pkl"
    feature_schema_version: str = "1.0"
    inference_cadence_minutes: int = 60  # How often to run ML inference
    confidence_threshold: float = 0.5  # Minimum confidence for AVAILABLE status
    min_training_samples: int = 100  # Minimum samples before model is ACTIVE
    # RUL stability
    rul_stability_window_hours: int = 24  # Window for stability check
    rul_max_change_per_window_pct: float = 30.0  # Max % change per window


@dataclass
class BaselineConfig:
    """Configuration for baseline computation."""

    window_hours: int = 168  # 1 week
    min_samples: int = 100
    update_cadence_hours: int = 24
    min_samples_for_baseline: int = 50


@dataclass
class ModelConfig:
    """Configuration for ML model."""

    model_path: str = "/app/models/rul_model.pkl"
    feature_schema_version: str = "1.0"
    inference_cadence_minutes: int = 60
    confidence_threshold: float = 0.5
    min_training_samples: int = 100
    # Validation
    validation_split: float = 0.2
    time_aware_split: bool = True
    min_validation_samples: int = 20


@dataclass
class AlertConfig:
    """Configuration for alert behavior."""

    # Deduplication
    dedup_window_hours: int = 24
    # Cooldown
    cooldown_minutes: int = 60
    # Persistence
    persistence_required_readings: int = 2
    # Auto-clear
    auto_clear_enabled: bool = True
    # Cooldown per alert code (minutes)
    cooldown_by_code: Dict[str, int] = field(
        default_factory=lambda: {
            "leak_detected": 120,
            "pressure_high": 60,
            "pressure_low": 60,
            "flow_low": 30,
            "flow_interrupted": 120,
            "pump_overcurrent": 120,
            "water_quality_degraded": 60,
            "filter_stress_high": 120,
            "filter_health_critical": 180,
            "tank_level_low": 30,
        }
    )


# Default configurations
DEFAULT_FILTER_STRESS_CONFIG = FilterStressConfig()
DEFAULT_FILTER_HEALTH_CONFIG = FilterHealthConfig()
DEFAULT_RUL_CONFIG = RULConfig()
DEFAULT_BASELINE_CONFIG = BaselineConfig()
DEFAULT_MODEL_CONFIG = ModelConfig()
DEFAULT_ALERT_CONFIG = AlertConfig()


# FSI Config Version tracking
@dataclass
class FSIConfigVersion:
    version: str
    effective_from: datetime
    weights: Dict[str, float]
    thresholds: Dict[str, float]
    units: Dict[str, str]
    description: str


FSI_CONFIG_VERSIONS = [
    FSIConfigVersion(
        version="1.0",
        effective_from=datetime(2026, 1, 1),
        weights={
            "differential_pressure": 0.25,
            "flow_deviation": 0.20,
            "turbidity_exposure": 0.15,
            "cumulative_volume": 0.15,
            "filter_age": 0.10,
            "operating_hours": 0.08,
            "tds_trend": 0.07,
        },
        thresholds={
            "dp_low_threshold": 50.0,
            "dp_high_threshold": 200.0,
            "flow_dev_low_threshold": 5.0,
            "flow_dev_high_threshold": 20.0,
            "turbidity_exposure_low": 10.0,
            "turbidity_exposure_high": 100.0,
            "cum_volume_low": 1000.0,
            "cum_volume_high": 10000.0,
            "age_low": 90.0,
            "age_high": 365.0,
            "op_hours_low": 500.0,
            "op_hours_high": 2000.0,
        },
        units={
            "differential_pressure": "kPa",
            "flow_deviation": "%",
            "turbidity_exposure": "NTU-hours",
            "cumulative_volume": "L",
            "filter_age": "days",
            "operating_hours": "hours",
            "tds_trend": "% increase",
        },
        description="Initial FSI configuration",
    ),
]


# Baseline data structures
@dataclass
class BaselineMetrics:
    device_id: UUID
    timestamp: datetime
    window_hours: int
    sample_count: int
    flow_baseline_lpm: Optional[float] = None
    pressure_baseline_kpa: Optional[float] = None
    outlet_pressure_baseline_kpa: Optional[float] = None
    delta_pressure_baseline_kpa: Optional[float] = None
    turbidity_baseline_ntu: Optional[float] = None
    tds_baseline_ppm: Optional[float] = None
    daily_volume_baseline_l: Optional[float] = None
    pressure_stability_cv: Optional[float] = None  # coefficient of variation
    flow_stability_cv: Optional[float] = None
    sufficient_samples: bool = False
    calculation_version: str = "1.0"


@dataclass
class BaselineStatus:
    device_id: UUID
    is_established: bool
    metrics: Optional[BaselineMetrics] = None
    needed_samples: int = 0
    status: str = "BASELINE_ESTABLISHING"  # BASELINE_ESTABLISHING, ESTABLISHED, STALE


@dataclass
class CounterfactualAnalysis:
    """What-changed analysis for prediction changes."""

    device_id: UUID
    timestamp: datetime
    previous_rul_days: Optional[float] = None
    current_rul_days: Optional[float] = None
    rul_change_days: Optional[float] = None
    rul_change_pct: Optional[float] = None
    contributing_changes: List[Dict[str, Any]] = field(default_factory=list)
    # Each change: {"feature": "dp", "previous": 120, "current": 150, "change": 30, "contribution_to_rul_change": -5}
    narrative: str = ""


@dataclass
class RULStabilityReport:
    """Report on RUL prediction stability."""

    device_id: UUID
    timestamp: datetime
    window_hours: int
    readings_count: int
    rul_values: List[float]
    max_change_pct: float
    is_stable: bool
    instability_reason: Optional[str] = None


# Model Registry
@dataclass
class ModelArtifact:
    model_id: str
    model_type: str  # "rul_regression", "anomaly_detection", etc.
    version: str
    dataset_version: str
    feature_schema_version: str
    training_timestamp: datetime
    validation_timestamp: Optional[datetime] = None
    metrics: Dict[str, float] = field(default_factory=dict)
    status: str = "development"  # development, validation, active, retired
    artifact_path: str = ""
    notes: str = ""
    # Validation
    validation_metrics: Dict[str, float] = field(default_factory=dict)
    validation_split: float = 0.2
    time_aware_split: bool = True
    validation_samples: int = 0
    # Time-aware validation
    train_time_window: Optional[str] = None
    validation_time_window: Optional[str] = None


@dataclass
class DatasetMetadata:
    dataset_id: str
    dataset_type: DatasetType
    source: str  # device_id, experiment_id, etc.
    date_range: tuple  # (start, end)
    schema_version: str
    created_at: datetime
    preprocessing_version: str
    record_count: int
    notes: str = ""


# Dataset provenance tracking
@dataclass
class DatasetProvenance:
    dataset_id: str
    parent_dataset_ids: List[str] = field(default_factory=list)
    transformation: str = ""  # e.g., "filtered", "aggregated", "augmented"
    created_at: datetime = field(default_factory=datetime.utcnow)
    created_by: str = "system"
    description: str = ""


# Experiment mode
@dataclass
class ExperimentRecord:
    experiment_id: str
    experiment_type: str  # "filter_test", "membrane_test", "sensor_calibration", etc.
    start_time: datetime
    end_time: Optional[datetime] = None
    filter_id: Optional[str] = None
    filter_condition: str = ""  # "new", "aged", "fouled", "cleaned"
    water_condition: str = ""  # "municipal", "well", "brackish", "seawater"
    flow_lpm: Optional[float] = None
    pressure_kpa: Optional[float] = None
    temperature_c: Optional[float] = None
    turbidity_ntu: Optional[float] = None
    tds_ppm: Optional[float] = None
    duration_hours: Optional[float] = None
    volume_l: Optional[float] = None
    notes: str = ""
    recorded_by: str = ""
    # Sensor readings during experiment
    sensor_readings: List[Dict[str, Any]] = field(default_factory=list)
    # Annotations
    annotations: List[Dict[str, Any]] = field(default_factory=list)
    # Tags for filtering
    tags: List[str] = field(default_factory=list)
