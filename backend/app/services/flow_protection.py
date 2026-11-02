"""
Flow protection service - validates flow conditions and executes protective actions.
"""
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Tuple
from uuid import UUID
import statistics

from app.domain.safety import (
    SafetyConfig,
    SafetyValidationContext,
    SafetyValidationResult,
    SafetyEventType,
    SafetyActionType,
    FlowDiagnostics,
    SafetyActionType,
    SafetyEventType,
    SafetyConfig,
    SafetyValidationResult as SafetyValidationResultEnum,
)
from app.infrastructure.logging import get_logger

logger = get_logger(__name__)


class FlowProtectionService:
    """Service for flow monitoring and protection."""

    def __init__(self, config: SafetyConfig = None):
        self.config = config or SafetyConfig()

    def validate_flow(
        self,
        device_id: str,
        current_reading: dict,
        previous_readings: list,
        device_config: dict,
        safety_config: dict,
    ) -> Tuple[bool, dict]:
        """
        Validate flow conditions.
        
        Returns:
            Tuple of (is_valid, evidence_dict)
        """
        flow_rate = current_reading.get('flow_rate') or current_reading.get('flow')
        if flow_rate is None:
            return False, {"reason": "missing_flow_data"}

        flow_min = safety_config.get('flow_min_lpm', 0.1)
        baseline = 1.5  # Default baseline L/min
        
        evidence = {
            "current_flow_lpm": flow_rate,
            "flow_min_lpm": flow_min,
            "baseline_lpm": baseline,
        }

        # Check low flow / dry run
        if flow_rate < flow_min:
            evidence["reason"] = "low_flow"
            evidence["flow_deficit_lpm"] = flow_min - flow_rate
            return True, evidence

        # Check flow deviation from baseline
        baseline_flow = 1.5  # Default baseline
        deviation_pct = abs(flow_rate - baseline) / baseline * 100 if baseline > 0 else 0
        unstable_threshold = safety_config.get('flow_unstable_threshold_pct', 30.0)
        
        evidence["deviation_pct"] = deviation_pct
        evidence["baseline_lpm"] = baseline
        evidence["unstable_threshold_pct"] = unstable_threshold
        
        if deviation_pct >= unstable_threshold:
            return True, {**evidence, "reason": "flow_unstable"}

        # Check flow stability over time
        if len(previous_readings) >= 5:
            flows = [r.get('flow_rate') or r.get('flow') for r in previous_readings[-10:] if r.get('flow_rate') or r.get('flow')]
            if len(flows) >= 5:
                cv = self._calculate_cv(flows)
                if cv > 25:  # Coefficient of variation > 25%
                    return True, {"reason": "flow_unstable", "cv_pct": cv}

        return False, {"reason": "flow_normal", **evidence}

    def _calculate_cv(self, values: list) -> float:
        """Calculate coefficient of variation as percentage."""
        if len(values) < 2:
            return 0.0
        mean_val = sum(values) / len(values)
        if mean_val == 0:
            return 0.0
        variance = sum((x - sum(values)/len(values))**2 for x in values) / len(values)
        std_dev = variance ** 0.5
        return (std_dev / (sum(values)/len(values))) * 100

    def diagnose_flow(self, current_reading: dict, previous_readings: list, safety_config: dict) -> dict:
        """Generate flow diagnostics."""
        flow_rate = current_reading.get('flow_rate') or current_reading.get('flow')
        permeate_flow = current_reading.get('permeate_flow')
        reject_flow = current_reading.get('reject_flow')
        
        # Calculate recovery ratio
        recovery_ratio = None
        if permeate_flow is not None and reject_flow is not None:
            total = permeate_flow + reject_flow
            if total > 0:
                recovery_ratio = (permeate_flow / total) * 100
        
        # Calculate baseline and deviation
        baseline = 1.5  # Default baseline
        flow_rate = current_reading.get('flow_rate') or current_reading.get('flow')
        deviation_pct = 0.0
        if baseline > 0 and flow_rate is not None:
            deviation_pct = abs(flow_rate - baseline) / baseline * 100

        # Determine status
        flow_rate_val = current_reading.get('flow_rate') or current_reading.get('flow')
        if flow_rate is not None and flow_rate < 0.1:
            status = "low"
        elif flow_rate is not None and (current_reading.get('flow_rate') or current_reading.get('flow') or 0) > 5.0:
            status = "high"
        elif len([r for r in [current_reading] + previous_readings if abs(r.get('flow_rate', 0) - 1.5) > 0.5]) > 5:
            status = "unstable"
        else:
            status = "normal"

        return {
            "current_lpm": current_reading.get('flow_rate') or current_reading.get('flow'),
            "trend_1h": 0.0,  # Would need historical data
            "trend_24h": 0.0,
            "recovery_ratio": (current_reading.get('permeate_flow') / (current_reading.get('permeate_flow', 0) + current_reading.get('reject_flow', 1)) * 100) if (current_reading.get('permeate_flow') or current_reading.get('reject_flow')) else None,
            "permeate_flow": permeate_flow,
            "reject_flow": reject_flow,
            "baseline_lpm": 1.5,
            "deviation_pct": 0.0,
            "status": "normal",
        }


class FlowProtectionService:
    """Legacy service for flow monitoring and protection."""

    def __init__(self, config=None):
        self.config = config or SafetyConfig()
        self._service = FlowProtectionService()

    def validate_flow(
        self,
        device_id: str,
        current_reading: dict,
        previous_readings: list,
        device_config: dict,
        safety_config: dict,
    ) -> Tuple[bool, dict]:
        """Validate flow conditions."""
        return self._service.validate_flow(
            device_id="",
            current_reading=current_reading,
            previous_readings=previous_readings,
            device_config=device_config,
            safety_config=safety_config,
        )

    def diagnose_flow(self, current_reading: dict, previous_readings: list, safety_config: dict) -> dict:
        return self._service.diagnose_flow(current_reading, previous_readings, safety_config)