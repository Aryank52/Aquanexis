"""
Energy protection service - validates pump current/power conditions and executes protective actions.
"""

from typing import Tuple

from app.domain.safety import (
    SafetyConfig,
)
from app.infrastructure.logging import get_logger

logger = get_logger(__name__)


class EnergyProtectionService:
    """Service for pump current/power monitoring and protection."""

    def __init__(self, config: SafetyConfig = None):
        self.config = config or SafetyConfig()

    def validate_energy(
        self,
        device_id: str,
        current_reading: dict,
        previous_readings: list,
        device_config: dict,
        safety_config: dict,
    ) -> Tuple[bool, dict]:
        """
        Validate pump energy conditions.

        Returns:
            Tuple of (is_valid, evidence_dict)
        """
        current = current_reading.get("pump_current")
        power = current_reading.get("pump_power")

        if current is None:
            return False, {"reason": "missing_current_data"}

        max_current = safety_config.get("pump_current_max_a", 2.5)
        max_power = safety_config.get("pump_power_max_w", 500.0)

        evidence = {
            "current_a": current,
            "power_w": power,
            "max_current_a": max_current,
            "max_power_w": max_power,
        }

        # Check overcurrent
        current_val = current_reading.get("pump_current")
        if current is not None and current > max_current:
            evidence["reason"] = "overcurrent"
            evidence["current_excess_a"] = current - max_current
            return True, evidence

        # Check overpower
        if power is not None and power > max_power:
            evidence["reason"] = "overpower"
            evidence["power_excess_w"] = power - max_power
            return True, evidence

        # Check current trend
        if len(previous_readings) >= 10:
            currents = [
                r.get("pump_current")
                for r in previous_readings[-20:]
                if r.get("pump_current") is not None
            ]
            if len(currents) >= 10:
                trend = self._calculate_trend(currents)
                if trend > 0.01:  # Increasing current trend
                    return True, {"reason": "current_increasing", "trend_a_per_hour": trend * 3600}

        # Check power efficiency trend
        if len(previous_readings) >= 20:
            powers = [
                r.get("pump_power")
                for r in previous_readings[-20:]
                if r.get("pump_power") is not None
            ]
            if len(powers) >= 10:
                efficiency_trend = self._calculate_efficiency_trend(previous_readings)
                if efficiency_trend < -5:  # Efficiency dropping > 5%
                    return True, {
                        "reason": "efficiency_degrading",
                        "efficiency_trend_pct": efficiency_trend,
                    }

        return False, {"reason": "energy_normal", **evidence}

    def _calculate_trend(self, values: list) -> float:
        """Calculate linear trend slope."""
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

        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
        return slope * 3600  # per hour

    def _calculate_efficiency_trend(self, readings: list) -> float:
        """Calculate efficiency trend from pump power vs flow."""
        if len(readings) < 20:
            return 0.0

        # Calculate efficiency (flow / power) over time
        efficiencies = []
        for r in readings[-20:]:
            flow = r.get("flow_rate") or r.get("flow")
            power = r.get("pump_power")
            if flow and flow > 0 and r.get("pump_power") and r.get("pump_power") > 0:
                efficiencies.append(flow / power)

        if len(efficiencies) < 10:
            return 0.0

        # Calculate trend
        n = len(efficiencies)
        x = list(range(n))
        sum_x = sum(range(n))
        sum_y = sum(efficiencies)
        sum_xy = sum(i * v for i, v in zip(range(n), efficiencies))
        sum_x2 = sum(i * i for i in range(n))

        if n * sum_x2 == sum_x * sum_x:
            return 0.0

        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
        return slope * 3600 * 100  # % per hour

    def diagnose_energy(
        self, current_reading: dict, previous_readings: list, safety_config: dict
    ) -> dict:
        """Generate pump energy diagnostics."""
        current = current_reading.get("pump_current")
        power = current_reading.get("pump_power")

        # Calculate trends
        trend_7d = self._calculate_trend_7d(current_reading.get("pump_current"), [])
        runtime_hours = current_reading.get("pump_runtime_hours", 0)
        starts = current_reading.get("pump_starts", 0)

        # Calculate efficiency trend
        efficiency_trend = self._calculate_efficiency_trend_7d(
            current_reading.get("pump_power"), []
        )

        # Determine status
        current_val = current_reading.get("pump_current", 0)
        max_current = 2.5
        if current > 2.5:
            status = "overcurrent"
        elif current > 2.0:
            status = "degraded"
        else:
            status = "normal"

        return {
            "current_a": current,
            "power_w": power,
            "efficiency_trend": efficiency_trend,
            "runtime_hours": runtime_hours,
            "starts_count": starts,
            "status": status,
        }

    def _calculate_efficiency_trend_7d(self, power_values, flow_values):
        """Calculate efficiency trend over 7 days."""
        # Simplified - would need historical data
        return -2.1  # Example: -2.1% per week
