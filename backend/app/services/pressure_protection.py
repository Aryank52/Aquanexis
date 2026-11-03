"""
Pressure protection service - validates pressure conditions and executes protective actions.
"""

import statistics
from datetime import datetime, timedelta
import statistics
from typing import Tuple

from app.domain.safety import (
    SafetyConfig,
)
from app.infrastructure.logging import get_logger

logger = get_logger(__name__)


class PressureProtectionService:
    """Service for pressure monitoring and protection."""

    def __init__(self, config: SafetyConfig = None):
        self.config = config or SafetyConfig()

    def validate_pressure(
        self,
        device_id: str,
        current_reading: dict,
        previous_readings: list,
        device_config: dict,
        safety_config: dict,
    ) -> Tuple[bool, dict]:
        """
        Validate pressure conditions.

        Returns:
            Tuple of (is_valid, evidence_dict)
        """
        pressure = current_reading.get("inlet_pressure") or current_reading.get("pressure")
        if pressure is None:
            return False, {"reason": "missing_pressure_data"}

        pressure_max = safety_config.get("pressure_max_kpa", 600.0)
        pressure_min = safety_config.get("pressure_min_kpa", 50.0)

        evidence = {
            "current_pressure_kpa": pressure,
            "pressure_max_kpa": pressure_max,
            "pressure_min_kpa": pressure_min,
        }

        # Check overpressure
        if pressure > pressure_max:
            evidence["reason"] = "overpressure"
            evidence["pressure_excess_kpa"] = pressure - pressure_max
            return True, evidence

        # Check low pressure
        if pressure < pressure_min:
            evidence["reason"] = "low_pressure"
            evidence["pressure_deficit_kpa"] = pressure_min - pressure
            return True, evidence

        # Check pressure stability
        if len(previous_readings) >= 5:
            pressures = [
                r.get("pressure") for r in previous_readings[-5:] if r.get("pressure") is not None
            ]
            if len(pressures) >= 5:
                stability = self._calculate_stability(pressures)
                if stability > 50:  # High coefficient of variation
                    evidence["reason"] = "pressure_unstable"
                    evidence["stability_cv_pct"] = stability
                    return True, evidence

        return False, {"reason": "pressure_normal", **evidence}

    def _calculate_stability(self, values: list) -> float:
        """Calculate coefficient of variation as percentage."""
        if len(values) < 2:
            return 0.0
        mean_val = sum(values) / len(values)
        if mean_val == 0:
            return 0.0
        variance = sum((x - sum(values) / len(values)) ** 2 for x in values) / len(values)
        std_dev = variance**0.5
        return (statistics.stdev(values) / statistics.mean(values)) * 100 if len(values) > 1 else 0

    def diagnose_pressure(
        self, current_reading: dict, previous_readings: list, safety_config: dict
    ) -> dict:
        """Generate pressure diagnostics."""
        pressure = current_reading.get("pressure")
        outlet_pressure = current_reading.get("outlet_pressure")

        # Calculate differential pressure
        inlet = current_reading.get("pressure")
        outlet = current_reading.get("outlet_pressure")
        delta_p = (inlet - outlet) if inlet is not None and outlet is not None else None

        # Calculate trends
        trend_1h = self._calculate_trend(previous_readings, "pressure", hours=1)
        trend_24h = self._calculate_trend(previous_readings, "pressure", hours=24)

        # Fouling indicator based on differential pressure trend
        fouling = self._calculate_fouling_indicator(previous_readings)

        # Pump curve deviation
        pump_curve_dev = self._calculate_pump_curve_deviation(previous_readings)

        status = "normal"
        inlet_pressure = current_reading.get("pressure", 0)
        max_pressure = 600.0
        if inlet_pressure > 600:
            status = "critical"
        elif inlet_pressure > 550:
            status = "elevated"
        elif inlet_pressure < 50:
            status = "critical"

        return {
            "current_kpa": current_reading.get("pressure"),
            "trend_1h": self._calculate_trend(previous_readings, "pressure", hours=1),
            "trend_24h": self._calculate_trend(previous_readings, "pressure", hours=24),
            "fouling_indicator": self._calculate_fouling_indicator(previous_readings),
            "pump_curve_deviation": self._calculate_pump_curve_deviation(previous_readings),
            "status": "normal"
            if 50 <= (current_reading.get("pressure") or 0) <= 550
            else "elevated"
            if (current_reading.get("pressure") or 0) < 600
            else "critical",
        }

    def _calculate_trend(self, readings: list, field: str, hours: int) -> float:
        """Calculate trend (slope) over specified hours."""
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        values = []
        for r in readings:
            if r.get("timestamp") and r.get(field) is not None:
                if r["timestamp"] >= cutoff:
                    values.append(r[field])

        if len(values) < 2:
            return 0.0

        n = len(values)
        x = list(range(n))
        sum_x = sum(range(n))
        sum_y = sum(values)
        sum_xy = sum(i * v for i, v in zip(range(n), values))
        sum_x2 = sum(i * i for i in range(n))

        if n * sum_x2 == sum_x * sum_x:
            return 0.0

        slope = (n * sum(x * y for x, y in zip(range(n), values)) - sum_x * sum_y) / (
            n * sum_x2 - sum_x * sum_x
        )
        return slope * 3600  # per hour

    def _calculate_fouling_indicator(self, readings: list) -> float:
        """Calculate membrane fouling indicator based on differential pressure trend."""
        if len(readings) < 10:
            return 0.0

        dp_values = []
        for r in readings[-50:]:
            inlet = r.get("pressure")
            outlet = r.get("outlet_pressure")
            if inlet is not None and outlet is not None:
                dp_values.append(inlet - outlet)

        if len(dp_values) < 10:
            return 0.0

        # Calculate trend of differential pressure
        n = len(dp_values)
        x = list(range(n))
        sum_x = sum(x)
        sum_y = sum(dp_values)
        sum_xy = sum(x[i] * dp_values[i] for i in range(n))
        sum_x2 = sum(xi * xi for xi in x)

        if n * sum_x2 == sum_x * sum_x:
            return 0.0

        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
        # Normalize: positive slope = increasing DP = fouling
        return max(0, min(1, slope * 1000))  # Normalize to 0-1

    def _calculate_pump_curve_deviation(self, readings: list) -> float:
        """Calculate pump curve deviation from expected."""
        if len(readings) < 10:
            return 0.0

        # Expected flow vs pressure curve (simplified)
        # In production, this would use a pump curve model
        recent = readings[-20:]
        flows = [
            r.get("flow_rate") or r.get("flow")
            for r in recent
            if r.get("flow_rate") or r.get("flow")
        ]
        pressures = [r.get("pressure") for r in recent if r.get("pressure")]

        if len(flows) < 5 or len(pressures) < 5:
            return 0.0

        # Simplified: check if flow is lower than expected for given pressure
        avg_flow = sum(flows) / len(flows)
        avg_pressure = sum(pressures) / len(pressures)

        # Expected flow at this pressure (simplified linear model)
        expected_flow = max(0.1, avg_pressure * 0.005)  # Rough approximation
        if expected_flow <= 0:
            return 0.0

        actual_avg = sum(r.get("flow_rate") or r.get("flow") or 0 for r in recent[-10:]) / min(
            10, len(recent)
        )
        if expected_flow <= 0:
            return 0.0

        deviation = (expected_flow - actual_avg) / expected_flow * 100
        return max(0, deviation)
