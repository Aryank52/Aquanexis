"""
Leak protection service - validates leak conditions and executes protective actions.
"""
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Tuple
from uuid import UUID

from app.domain.safety import (
    SafetyConfig,
    SafetyValidationContext,
    SafetyValidationResult,
    SafetyValidationResult,
    SafetyEventType,
    SafetyActionType,
    LeakDiagnostics,
    SafetyActionType,
    SafetyEventType,
    SafetyConfig,
    SafetyValidationResult as SafetyValidationResultEnum,
)
from app.infrastructure.logging import get_logger

logger = get_logger(__name__)


class LeakProtectionService:
    """Service for leak detection and protection."""

    def __init__(self, config: SafetyConfig = None):
        self.config = config or SafetyConfig()

    def validate_leak(
        self,
        device_id: str,
        current_reading: dict,
        previous_readings: list,
        device_config: dict,
        safety_config: dict,
    ) -> Tuple[bool, dict]:
        """
        Validate leak condition.
        
        Returns:
            Tuple of (is_valid, evidence_dict)
        """
        leak_detected = current_reading.get('leak_detected', False)
        if not leak_detected:
            return False, {"reason": "leak_sensor_not_triggered"}

        # Check persistence
        persistence = safety_config.get('leak_persistence_readings', 2)
        leak_count = 0
        for reading in [current_reading] + previous_readings:
            if reading.get('leak_detected'):
                leak_count += 1

        if leak_count < persistence:
            return False, {
                "reason": "insufficient_persistence",
                "leak_count": leak_count,
                "required": persistence
            }

        # Validate with correlated sensors if configured
        validate_with = safety_config.get('leak_validate_with', ['flow_delta', 'pressure_drop'])
        evidence = {
            "leak_sensor": True,
            "persistence_readings": leak_count,
        }

        if 'flow_delta' in validate_with:
            flow_delta = self._calculate_flow_delta(current_reading, previous_readings)
            evidence['flow_delta_lpm'] = flow_delta
            if flow_delta is not None and flow_delta > 0.1:  # Significant flow increase
                evidence['flow_correlated'] = True

        if 'pressure_drop' in validate_with:
            pressure_drop = self._calculate_pressure_drop(current_reading, previous_readings)
            evidence['pressure_drop_kpa'] = pressure_drop
            if pressure_drop is not None and pressure_drop > 10:  # kPa
                evidence['pressure_correlated'] = True

        # Require at least one correlation
        correlated = evidence.get('flow_correlated', False) or evidence.get('pressure_correlated', False)
        if not correlated:
            return False, {**evidence, "reason": "no_sensor_correlation"}

        return True, evidence

    def _calculate_flow_delta(self, current: dict, previous_readings: list) -> Optional[float]:
        """Calculate flow rate change from previous readings."""
        if not previous_readings:
            return None
        current_flow = current.get('flow_rate') or current.get('flow')
        if current_flow is None:
            return None
        
        prev_flow = previous_readings[0].get('flow_rate') or previous_readings[0].get('flow')
        if prev_flow is None:
            return None
            
        return current_flow - prev_flow

    def _calculate_pressure_drop(self, current: dict, previous_readings: list) -> Optional[float]:
        """Calculate pressure drop from previous readings."""
        if not previous_readings:
            return None
            
        current_pressure = current.get('inlet_pressure') or current.get('pressure')
        if current_pressure is None:
            return None
            
        prev_pressure = previous_readings[0].get('inlet_pressure') or previous_readings[0].get('pressure')
        if prev_pressure is None:
            return None
            
        return prev_pressure - current_pressure

    def diagnose_leak(self, current_reading: dict, previous_readings: list) -> dict:
        """Generate leak diagnostics."""
        leak_detected = current_reading.get('leak_detected') or current_reading.get('leak', False)
        flow_delta = self._calculate_flow_delta(current_reading, previous_readings)
        pressure_drop = self._calculate_pressure_drop(current_reading, previous_readings)
        
        # Count persistence
        persistence_readings = 0
        for reading in [current_reading] + previous_readings:
            if reading.get('leak_detected') or reading.get('leak'):
                persistence_readings += 1

        if leak_detected and persistence_readings >= 2:
            status = "leak_confirmed"
            probability = 0.95
        elif leak_detected:
            status = "suspect"
            probability = 0.6
        else:
            status = "dry"
            probability = 0.01

        return {
            "leak_detected": bool(leak_detected),
            "leak_probability": probability,
            "flow_delta_lpm": flow_delta,
            "pressure_drop_kpa": pressure_drop,
            "sensor_state": bool(leak_detected),
            "persistence_readings": persistence_readings,
            "status": status,
        }
