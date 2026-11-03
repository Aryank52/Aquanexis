"""
Filter Stress service - computes Filter Stress Index (deterministic).
Enhanced with baseline tracking, versioned config, and pressure differential as first-class feature.
"""
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from uuid import UUID

from app.domain.filter_intelligence import (
    FilterStressIndex,
    FilterStressState,
    FilterStressConfig,
    DEFAULT_FILTER_STRESS_CONFIG,
    FSIConfigVersion,
    FSIConfigVersion,
    BaselineMetrics,
    BaselineStatus,
    FSIConfigVersion,
    CounterfactualAnalysis,
)

from app.services.baseline_service import BaselineService


class FilterStressService:
    """Service for computing Filter Stress Index (deterministic)."""

    def __init__(self, config: FilterStressConfig = None):
        self.config = config or DEFAULT_FILTER_STRESS_CONFIG
        self.baseline_service = BaselineService()
        self._config_version = "1.0"

    async def compute_filter_stress(
        self,
        reading,
        previous_readings: List = None,
        device_config: Dict = None,
        filter_install_date: datetime = None,
        cumulative_volume: float = 0.0,
        operating_hours: float = 0.0,
        device_id: UUID = None,
        baseline_service: 'BaselineService' = None,
    ) -> "FilterStressIndex":
        """
        Compute Filter Stress Index from current reading and context.
        
        Args:
            reading: Current sensor reading
            previous_readings: Previous readings for trend calculation
            device_config: Device-specific configuration
            filter_install_date: When the filter was installed
            cumulative_volume: Cumulative water processed (L)
            operating_hours: Total operating hours
            device_id: Device UUID for baseline tracking
            baseline_service: BaselineService instance for baseline tracking
            
        Returns:
            FilterStressIndex with state, score, and contributors
        """
        config = self._merge_config(device_config)
        self._config_version = "1.0"  # Would be loaded from registry in production
        
        # Get or create baseline for this device
        baseline_status = None
        baseline_metrics = None
        if baseline_service and device_id:
            baseline_status = await baseline_service.get_baseline_status(device_id)
            if baseline_status.is_established:
                baseline_metrics = baseline_status.metrics
        
        # Calculate component scores (0-100 each)
        component_scores = {}
        
        # 1. Differential pressure score (first-class feature)
        dp_score, dp_evidence = self._score_differential_pressure(reading, previous_readings, config, baseline_metrics)
        component_scores['differential_pressure'] = dp_score
        
        # 2. Flow deviation score
        flow_dev_score, flow_evidence = self._score_flow_deviation(reading, config, baseline_metrics)
        component_scores['flow_deviation'] = flow_dev_score
        
        # 3. Turbidity exposure score
        turbidity_score, turbidity_evidence = self._score_turbidity_exposure(reading, previous_readings, config)
        component_scores['turbidity_exposure'] = turbidity_score
        
        # 4. Cumulative volume score
        cum_volume_score = self._score_cumulative_volume(cumulative_volume, config)
        component_scores['cumulative_volume'] = cum_volume_score
        
        # 5. Filter age score
        age_score = self._score_filter_age(filter_install_date, config)
        component_scores['filter_age'] = age_score
        
        # 6. Operating hours score
        op_hours_score = self._score_operating_hours(operating_hours, config)
        component_scores['operating_hours'] = op_hours_score
        
        # 7. TDS trend score
        tds_trend_score = self._score_tds_trend(previous_readings, config)
        component_scores['tds_trend'] = tds_trend_score
        
        # Calculate weighted total (exclude missing primary sensor components from denominator)
        weights = {
            'differential_pressure': config.dp_weight,
            'flow_deviation': config.flow_dev_weight,
            'turbidity_exposure': config.turbidity_weight,
            'cumulative_volume': config.cum_volume_weight,
            'filter_age': config.age_weight,
            'operating_hours': config.op_hours_weight,
            'tds_trend': config.tds_trend_weight,
        }
        missing_components = set()
        if dp_evidence.get("reason") == "missing_pressure_data":
            missing_components.add("differential_pressure")
        if flow_evidence.get("reason") == "missing_flow_data":
            missing_components.add("flow_deviation")

        active_keys = [k for k in component_scores if k not in missing_components]
        weighted_sum = sum(
            component_scores.get(k, 0) * weights.get(k, 0)
            for k in active_keys
        )
        total_weight = sum(weights.get(k, 0) for k in active_keys)

        overall_score = (weighted_sum / total_weight) if total_weight > 0 else 0
        overall_score = max(0, min(100, overall_score))
        
        # Determine state
        if overall_score >= 70:
            state = FilterStressState.HIGH
        elif overall_score >= 40:
            state = FilterStressState.MODERATE
        else:
            state = FilterStressState.LOW
        
        # Build contributors list
        contributors = self._build_contributors(component_scores, config)
        
        # Build evidence
        evidence = self._build_evidence(
            reading, previous_readings, component_scores, config
        )
        if missing_components:
            evidence["missing_components"] = sorted(missing_components)
        
        # Add pressure differential as first-class feature
        inlet = getattr(reading, 'inlet_pressure', None)
        if inlet is None:
            inlet = getattr(reading, 'pressure', None)
        outlet = getattr(reading, 'outlet_pressure', None)
        pressure_diff = None
        if inlet is not None and outlet is not None:
            pressure_diff = round(inlet - outlet, 2)
        
        return FilterStressIndex(
            device_id=getattr(reading, 'device_id', UUID(int=0)),
            timestamp=getattr(reading, 'timestamp', datetime.utcnow()),
            state=state,
            score=round(overall_score, 1),
            contributors=contributors,
            evidence=evidence,
            calculation_version="2.0",  # Updated version for Phase E
            config_version=self._config_version,
            differential_pressure_score=component_scores.get('differential_pressure'),
            flow_deviation_score=component_scores.get('flow_deviation'),
            turbidity_exposure_score=component_scores.get('turbidity_exposure'),
            cumulative_volume_score=component_scores.get('cumulative_volume'),
            filter_age_score=component_scores.get('filter_age'),
            operating_hours_score=component_scores.get('operating_hours'),
            tds_trend_score=component_scores.get('tds_trend'),
            # Pressure differential as first-class feature (kPa)
            pressure_differential_kpa=pressure_diff,
            pressure_differential_baseline_kpa=None,  # Would come from baseline service
            pressure_differential_rate_of_change_kpa_per_hour=None,  # Would come from trend analysis
        )
    
    def _merge_config(self, device_config: Dict) -> FilterStressConfig:
        """Merge device config with defaults."""
        if not device_config or 'filter_stress' not in device_config:
            return DEFAULT_FILTER_STRESS_CONFIG
        
        config = DEFAULT_FILTER_STRESS_CONFIG
        custom = device_config.get('filter_stress', {})
        for key, value in custom.items():
            if hasattr(config, key):
                setattr(config, key, value)
        return config
    
    # Component scoring functions (0-100)
    
    def _score_differential_pressure(self, reading, previous_readings, config, baseline_metrics=None) -> tuple:
        """Score based on differential pressure (0-100). Returns (score, evidence_dict)."""
        inlet = getattr(reading, 'inlet_pressure', None)
        if inlet is None:
            inlet = getattr(reading, 'pressure', None)
        outlet = getattr(reading, 'outlet_pressure', None)
        if inlet is None or outlet is None:
            return 0.0, {"reason": "missing_pressure_data"}
        
        dp = inlet - outlet
        evidence = {
            "inlet_pressure_kpa": inlet,
            "outlet_pressure_kpa": outlet,
            "differential_pressure_kpa": dp,
            "dp_low_threshold": config.dp_low_threshold,
            "dp_high_threshold": config.dp_high_threshold,
        }
        
        # Add baseline comparison if available
        if baseline_metrics and baseline_metrics.delta_pressure_baseline_kpa:
            baseline_dp = baseline_metrics.delta_pressure_baseline_kpa
            evidence["baseline_dp_kpa"] = baseline_dp
            evidence["dp_deviation_from_baseline_kpa"] = dp - baseline_dp
            evidence["dp_deviation_pct"] = ((dp - baseline_metrics.delta_pressure_baseline_kpa) / max(baseline_metrics.delta_pressure_baseline_kpa, 1)) * 100
        
        if dp <= config.dp_low_threshold:
            return 0.0, evidence
        elif dp >= config.dp_high_threshold:
            return 100.0, evidence
        else:
            # Linear interpolation
            score = ((dp - config.dp_low_threshold) / 
                    (config.dp_high_threshold - config.dp_low_threshold)) * 100
            return score, evidence
    
    def _score_flow_deviation(self, reading, config, baseline_metrics=None) -> tuple:
        """Score based on flow deviation from baseline."""
        flow = getattr(reading, 'flow_rate', None) or getattr(reading, 'flow', None)
        if flow is None:
            return 0.0, {"reason": "missing_flow_data"}
        
        # Use baseline if available, otherwise default
        baseline = 1.5  # L/min default
        if baseline_metrics and baseline_metrics.flow_baseline_lpm:
            baseline = baseline_metrics.flow_baseline_lpm
        
        if baseline <= 0:
            return 0.0, {"reason": "invalid_baseline"}
        
        deviation = abs(flow - baseline) / baseline * 100  # %
        evidence = {
            "flow_rate_lpm": flow,
            "baseline_flow_lpm": baseline,
            "deviation_pct": deviation,
            "flow_dev_low_threshold": config.flow_dev_low_threshold,
            "flow_dev_high_threshold": config.flow_dev_high_threshold,
        }
        
        if deviation <= config.flow_dev_low_threshold:
            return 0.0, evidence
        elif deviation >= config.flow_dev_high_threshold:
            return 100.0, evidence
        else:
            score = ((deviation - config.flow_dev_low_threshold) / 
                    (config.flow_dev_high_threshold - config.flow_dev_low_threshold)) * 100
            return score, evidence
    
    def _score_turbidity_exposure(self, reading, previous_readings, config) -> tuple:
        """Score based on cumulative turbidity exposure."""
        if not previous_readings:
            return 0.0, {"reason": "insufficient_history"}
        
        # Calculate cumulative NTU-hours
        turbidity_hours = 0.0
        for i in range(1, len(previous_readings)):
            prev = previous_readings[i-1]
            curr = previous_readings[i]
            prev_turb = getattr(prev, 'turbidity', None)
            curr_turb = getattr(curr, 'turbidity', None)
            prev_time = getattr(prev, 'timestamp', None)
            curr_time = getattr(curr, 'timestamp', None)
            
            if (prev_turb is not None and curr_turb is not None and 
                prev_time is not None and curr_time is not None):
                avg_turb = (prev_turb + curr_turb) / 2
                hours = (curr_time - prev_time).total_seconds() / 3600
                turbidity_hours += avg_turb * hours
        
        evidence = {
            "turbidity_hours": turbidity_hours,
            "turbidity_exposure_low": config.turbidity_exposure_low,
            "turbidity_exposure_high": config.turbidity_exposure_high,
        }
        
        if turbidity_hours <= config.turbidity_exposure_low:
            return 0.0, evidence
        elif turbidity_hours >= config.turbidity_exposure_high:
            return 100.0, evidence
        else:
            score = ((turbidity_hours - config.turbidity_exposure_low) / 
                    (config.turbidity_exposure_high - config.turbidity_exposure_low)) * 100
            return score, evidence
    
    def _score_cumulative_volume(self, volume: float, config) -> float:
        """Score based on cumulative water volume processed."""
        if volume <= config.cum_volume_low:
            return 0.0
        elif volume >= config.cum_volume_high:
            return 100.0
        else:
            return ((volume - config.cum_volume_low) / 
                    (config.cum_volume_high - config.cum_volume_low)) * 100
    
    def _score_filter_age(self, install_date: datetime, config) -> float:
        """Score based on filter age in days."""
        if install_date is None:
            return 0.0
        
        age_days = (datetime.utcnow() - install_date).days
        if age_days <= config.age_low:
            return 0.0
        elif age_days >= config.age_high:
            return 100.0
        else:
            return ((age_days - config.age_low) / 
                    (config.age_high - config.age_low)) * 100
    
    def _score_operating_hours(self, hours: float, config) -> float:
        """Score based on pump operating hours."""
        if hours <= config.op_hours_low:
            return 0.0
        elif hours >= config.op_hours_high:
            return 100.0
        else:
            return ((hours - config.op_hours_low) / 
                    (config.op_hours_high - config.op_hours_low)) * 100
    
    def _score_tds_trend(self, previous_readings, config) -> float:
        """Score based on TDS trend (increasing TDS = more stress)."""
        if not previous_readings or len(previous_readings) < 10:
            return 0.0
        
        # Calculate TDS trend over recent readings
        tds_values = [getattr(r, 'tds', None) for r in previous_readings[-20:]]
        tds_values = [v for v in tds_values if v is not None]
        
        if len(tds_values) < 10:
            return 0.0
        
        # Simple trend: compare recent vs older
        recent = tds_values[-5:]
        older = tds_values[-20:-5]
        if not recent or not older:
            return 0.0
        
        recent_avg = sum(recent) / len(recent)
        older_avg = sum(older) / len(older)
        
        if older_avg <= 0:
            return 0.0
        
        increase_pct = ((recent_avg - older_avg) / older_avg) * 100
        
        # More increase = more stress
        if increase_pct <= 0:
            return 0.0
        elif increase_pct >= 50:
            return 100.0
        else:
            return (increase_pct / 50) * 100
    
    def _merge_config(self, device_config: Dict) -> FilterStressConfig:
        """Merge device config with defaults."""
        if not device_config or 'filter_stress' not in device_config:
            return DEFAULT_FILTER_STRESS_CONFIG
        
        config = DEFAULT_FILTER_STRESS_CONFIG
        custom = device_config['filter_stress']
        for key, value in custom.items():
            if hasattr(config, key):
                setattr(config, key, value)
        return config
    
    def _build_contributors(self, scores: Dict, config) -> List[str]:
        """Build human-readable contributor list."""
        contributors = []
        threshold = 30  # Score threshold for significant contribution
        
        if scores.get('differential_pressure', 0) >= 30:
            contributors.append("differential_pressure_rising")
        if scores.get('flow_deviation', 0) >= 30:
            contributors.append("flow_deviation_negative")
        if scores.get('turbidity_exposure', 0) >= 30:
            contributors.append("turbidity_exposure_above_baseline")
        if scores.get('cumulative_volume', 0) >= 30:
            contributors.append("cumulative_volume_high")
        if scores.get('filter_age', 0) >= 30:
            contributors.append("filter_age_advanced")
        if scores.get('operating_hours', 0) >= 30:
            contributors.append("operating_hours_high")
        if scores.get('tds_trend', 0) >= 30:
            contributors.append("tds_trend_increasing")
        
        return contributors
    
    def _build_evidence(self, reading, previous_readings, scores, config) -> Dict:
        """Build evidence dictionary for transparency."""
        inlet = getattr(reading, 'inlet_pressure', None)
        if inlet is None:
            inlet = getattr(reading, 'pressure', None)
        outlet = getattr(reading, 'outlet_pressure', None)
        dp = round(inlet - outlet, 2) if (inlet is not None and outlet is not None) else None
        evidence = {
            "differential_pressure_kpa": dp,
            "flow_rate_lpm": getattr(reading, 'flow_rate', None) or getattr(reading, 'flow', None),
            "turbidity_ntu": getattr(reading, 'turbidity', None),
            "tds_ppm": getattr(reading, 'tds', None),
            "thresholds": {
                "dp_low": config.dp_low_threshold,
                "dp_high": config.dp_high_threshold,
                "flow_dev_low": config.flow_dev_low_threshold,
                "flow_dev_high": config.flow_dev_high_threshold,
            },
        }
        return evidence