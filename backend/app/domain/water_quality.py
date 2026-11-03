"""
Water Quality domain - AquaScore, trends, anomalies.
Pure Python, no framework dependencies.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import List, Optional
from uuid import UUID

from app.domain.readings import SensorReading


class TrendDirection(str, Enum):
    IMPROVING = "improving"
    STABLE = "stable"
    DEGRADING = "degrading"


class AnomalyType(str, Enum):
    ZSCORE = "zscore"
    IQR = "iqr"
    RATE_OF_CHANGE = "rate_of_change"
    ISOLATION_FOREST = "isolation_forest"


# WHO/EPA guideline limits for drinking water
GUIDELINES = {
    "tds": {"ideal": (0, 300), "acceptable": (300, 600), "unit": "ppm"},
    "conductivity": {"ideal": (0, 500), "acceptable": (500, 1000), "unit": "µS/cm"},
    "ph": {"ideal": (6.5, 8.5), "acceptable": (6.0, 9.0), "unit": ""},
    "turbidity": {"ideal": (0, 1), "acceptable": (1, 5), "unit": "NTU"},
    "temperature": {"ideal": (10, 25), "acceptable": (5, 35), "unit": "°C"},
}


@dataclass
class ParameterScore:
    """Score for a single water quality parameter."""

    parameter: str
    value: Optional[float]
    score: int  # 0-100
    guideline_min: Optional[float] = None
    guideline_max: Optional[float] = None
    unit: str = ""
    status: str = "unknown"  # ideal, acceptable, poor


@dataclass
class TrendPoint:
    """Single point in a trend series."""

    timestamp: datetime
    value: float


@dataclass
class TrendAnalysis:
    """Trend analysis for a parameter over a time window."""

    parameter: str
    window: str  # "1h", "24h", "7d", "30d"
    direction: TrendDirection
    magnitude: float  # % change
    points: List[TrendPoint] = field(default_factory=list)
    slope_per_hour: float = 0.0


@dataclass
class AnomalyFlag:
    """Anomaly detection result for a parameter."""

    parameter: str
    score: float
    threshold: float
    type: AnomalyType
    message: str = ""


@dataclass
class AquaScore:
    """Complete water quality score."""

    device_id: UUID
    timestamp: datetime
    overall_score: int  # 0-100
    parameter_scores: List[ParameterScore] = field(default_factory=list)
    trends: List[TrendAnalysis] = field(default_factory=list)
    anomaly_score: float = 0.0
    anomaly_flags: List[AnomalyFlag] = field(default_factory=list)
    data_freshness_seconds: int = 0


# Weight for each parameter in overall score
PARAMETER_WEIGHTS = {
    "tds": 0.30,
    "ph": 0.25,
    "turbidity": 0.20,
    "temperature": 0.10,
    "conductivity": 0.15,
}


def score_parameter(
    parameter: str,
    value: Optional[float],
    guideline_ideal: tuple = None,
    guideline_acceptable: tuple = None,
) -> ParameterScore:
    """Calculate score for a single parameter (0-100)."""
    if value is None:
        return ParameterScore(
            parameter=parameter,
            value=None,
            score=0,
            unit=GUIDELINES.get(parameter, {}).get("unit", ""),
            status="missing",
        )

    guidelines = GUIDELINES.get(parameter, {})
    ideal_min, ideal_max = guideline_ideal or guidelines.get("ideal", (0, 1000))
    accept_min, accept_max = guideline_acceptable or guidelines.get("acceptable", (0, 1000))

    if ideal_min <= value <= ideal_max:
        score = 100
        status = "ideal"
    elif accept_min <= value <= accept_max:
        # Linear interpolation between 60-100
        if value < ideal_min:
            score = 60 + 40 * (value - accept_min) / (ideal_min - accept_min)
        else:
            score = 60 + 40 * (accept_max - value) / (accept_max - ideal_max)
        score = max(60, min(100, int(score)))
        status = "acceptable"
    else:
        # Outside acceptable range - linear down to 0
        if value < accept_min:
            score = max(0, 60 * value / accept_min)
        else:
            score = max(0, 60 * (2 * accept_max - value) / accept_max)
        score = int(score)
        status = "poor"

    return ParameterScore(
        parameter=parameter,
        value=value,
        score=score,
        guideline_min=ideal_min,
        guideline_max=ideal_max,
        unit=guidelines.get("unit", ""),
        status=status,
    )


def compute_aquascore(readings, device_config=None) -> AquaScore:
    """
    Compute AquaScore from sensor readings.

    Args:
        readings: SensorReadingInput or similar with sensor values
        device_config: Optional device configuration for custom weights

    Returns:
        AquaScore with parameter scores, trends, and anomalies
    """
    device_id = getattr(readings, "device_id", UUID(int=0))
    timestamp = getattr(readings, "timestamp", datetime.utcnow())

    # Score each parameter
    parameter_scores = []
    total_weight = 0
    weighted_sum = 0

    for param, weight in PARAMETER_WEIGHTS.items():
        value = getattr(readings, param, None)
        if value is not None:
            param_score = score_parameter(param, value)
            parameter_scores.append(param_score)
            weighted_sum += param_score.score * weight
            total_weight += weight

    overall_score = int(weighted_sum / total_weight) if total_weight > 0 else 0

    return AquaScore(
        device_id=device_id,
        timestamp=timestamp,
        overall_score=overall_score,
        parameter_scores=parameter_scores,
        anomaly_score=0.0,  # Will be filled by anomaly detection
    )


def compute_trends(
    readings_history: List[SensorReading], windows: List[str] = None, parameters: List[str] = None
) -> List[TrendAnalysis]:
    """
    Compute trend analysis for multiple time windows.

    Args:
        readings_history: List of historical readings (newest first)
        windows: Time windows to analyze (e.g., ["1h", "24h", "7d"])
        parameters: Parameters to analyze

    Returns:
        List of TrendAnalysis objects
    """
    if not readings_history:
        return []

    windows = windows or ["1h", "24h", "7d"]
    parameters = parameters or ["tds", "ph", "turbidity", "temperature", "flow_rate"]

    # Parse window strings to timedeltas
    window_deltas = {
        "1h": timedelta(hours=1),
        "24h": timedelta(hours=24),
        "7d": timedelta(days=7),
        "30d": timedelta(days=30),
    }

    trends = []
    now = readings_history[0].timestamp if readings_history else datetime.utcnow()

    for window in windows:
        delta = window_deltas.get(window, timedelta(hours=24))
        cutoff = now - delta

        # Filter readings within window
        window_readings = [r for r in readings_history if r.timestamp >= cutoff]
        if len(window_readings) < 2:
            continue

        for param in parameters:
            values = [(r.timestamp, getattr(r, param, None)) for r in window_readings]
            values = [(ts, v) for ts, v in values if v is not None]

            if len(values) < 2:
                continue

            # Calculate trend
            timestamps = [(ts - values[0][0]).total_seconds() / 3600 for ts, _ in values]  # hours
            param_values = [v for _, v in values]

            # Simple linear regression for slope
            n = len(values)
            sum_x = sum(timestamps)
            sum_y = sum(param_values)
            sum_xy = sum(x * y for x, y in zip(timestamps, param_values))
            sum_x2 = sum(x * x for x in timestamps)

            slope = (
                (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
                if n * sum_x2 != sum_x * sum_x
                else 0
            )

            # Direction and magnitude
            mean_val = sum_y / n
            magnitude = (
                abs(slope * (timestamps[-1] - timestamps[0])) / mean_val * 100
                if mean_val != 0
                else 0
            )

            if slope > 0.01:
                direction = (
                    TrendDirection.DEGRADING
                    if param in ["tds", "turbidity", "conductivity"]
                    else TrendDirection.IMPROVING
                )
            elif slope < -0.01:
                direction = (
                    TrendDirection.IMPROVING
                    if param in ["tds", "turbidity", "conductivity"]
                    else TrendDirection.DEGRADING
                )
            else:
                direction = TrendDirection.STABLE

            trend_points = [TrendPoint(timestamp=ts, value=v) for ts, v in values]

            trends.append(
                TrendAnalysis(
                    parameter=param,
                    window=window,
                    direction=direction,
                    magnitude=magnitude,
                    points=trend_points,
                    slope_per_hour=slope,
                )
            )

    return trends


def detect_anomalies(
    readings_window: List[SensorReading],
    parameters: List[str] = None,
    zscore_threshold: float = 3.0,
    iqr_multiplier: float = 1.5,
) -> List[AnomalyFlag]:
    """
    Detect anomalies using statistical methods.

    Args:
        readings_window: Recent readings for analysis
        parameters: Parameters to check
        zscore_threshold: Z-score threshold for anomaly
        iqr_multiplier: IQR multiplier for outlier detection

    Returns:
        List of AnomalyFlag objects
    """
    if len(readings_window) < 10:
        return []  # Need minimum data for statistics

    parameters = parameters or ["tds", "ph", "turbidity", "temperature", "flow_rate"]
    anomalies = []

    for param in parameters:
        values = [getattr(r, param, None) for r in readings_window]
        values = [v for v in values if v is not None]

        if len(values) < 10:
            continue

        # Z-score detection
        mean_val = sum(values) / len(values)
        std_val = (sum((v - mean_val) ** 2 for v in values) / len(values)) ** 0.5

        if std_val > 0:
            latest = values[-1]
            zscore = abs(latest - mean_val) / std_val

            if zscore > zscore_threshold:
                anomalies.append(
                    AnomalyFlag(
                        parameter=param,
                        score=zscore,
                        threshold=zscore_threshold,
                        type=AnomalyType.ZSCORE,
                        message=f"Z-score {zscore:.2f} exceeds threshold {zscore_threshold}",
                    )
                )

        # IQR detection
        sorted_vals = sorted(values)
        n = len(sorted_vals)
        q1 = sorted_vals[n // 4]
        q3 = sorted_vals[3 * n // 4]
        iqr = q3 - q1

        if iqr > 0:
            lower_bound = q1 - iqr_multiplier * iqr
            upper_bound = q3 + iqr_multiplier * iqr
            latest = values[-1]

            if latest < lower_bound or latest > upper_bound:
                anomalies.append(
                    AnomalyFlag(
                        parameter=param,
                        score=max(abs(latest - lower_bound), abs(latest - upper_bound)) / iqr,
                        threshold=iqr_multiplier,
                        type=AnomalyType.IQR,
                        message=f"Value {latest} outside IQR bounds [{lower_bound:.2f}, {upper_bound:.2f}]",
                    )
                )

        # Rate of change detection
        if len(values) >= 2:
            rate = abs(values[-1] - values[-2])
            # Threshold: 3 standard deviations of rate
            rates = [abs(values[i] - values[i - 1]) for i in range(1, len(values))]
            if rates:
                rate_mean = sum(rates) / len(rates)
                rate_std = (sum((r - rate_mean) ** 2 for r in rates) / len(rates)) ** 0.5
                if rate_std > 0 and rate > rate_mean + 3 * rate_std:
                    anomalies.append(
                        AnomalyFlag(
                            parameter=param,
                            score=rate / rate_std if rate_std > 0 else 0,
                            threshold=3.0,
                            type=AnomalyType.RATE_OF_CHANGE,
                            message=f"Rate of change {rate:.2f} is anomalous",
                        )
                    )

    return anomalies
