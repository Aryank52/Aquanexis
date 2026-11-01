"""
Filter Intelligence domain - Filter Stress Index, Filter Health Index, RUL.
Pure Python, no framework dependencies.
"""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, List, Any
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
    # Raw component scores for transparency
    differential_pressure_score: Optional[float] = None
    flow_deviation_score: Optional[float] = None
    turbidity_exposure_score: Optional[float] = None
    cumulative_volume_score: Optional[float] = None
    filter_age_score: Optional[float] = None
    operating_hours_score: Optional[float] = None
    tds_trend_score: Optional[float] = None


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
    calculation_version: str = "1.0"
    # Component breakdown
    stress_component: Optional[float] = None
    lifecycle_component: Optional[float] = None
    usage_component: Optional[float] = None
    pressure_flow_component: Optional[float] = None
    historical_behavior_component: Optional[float] = None


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
    recovery_ratio: Optional[float] = None  # calculated from flows
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
    op_hours_weight: float = 0.10
    
    # TDS trend
    tds_trend_weight: float = 0.10


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


@dataclass
class RULConfig:
    """Configuration for RUL prediction."""
    model_path: str = "/app/models/rul_model.pkl"
    feature_schema_version: str = "1.0"
    inference_cadence_minutes: int = 60  # How often to run ML inference
    confidence_threshold: float = 0.5  # Minimum confidence for AVAILABLE status
    min_training_samples: int = 100  # Minimum samples before model is ACTIVE


# Default configurations
DEFAULT_FILTER_STRESS_CONFIG = FilterStressConfig()
DEFAULT_FILTER_HEALTH_CONFIG = FilterHealthConfig()
DEFAULT_RUL_CONFIG = RULConfig()