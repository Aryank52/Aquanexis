"""
Filter Health service - computes Filter Health Index from stress and lifecycle.
"""
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from uuid import UUID

from app.domain.filter_intelligence import (
    FilterHealthIndex,
    FilterHealthState,
    FilterHealthConfig,
    DEFAULT_FILTER_HEALTH_CONFIG,
    FilterStressState,
)


class FilterHealthService:
    """Service for computing Filter Health Index."""

    def __init__(self, config: FilterHealthConfig = None):
        self.config = config or DEFAULT_FILTER_HEALTH_CONFIG

    def compute_filter_health(
        self,
        filter_stress: "FilterStressIndex",
        filter_install_date: datetime = None,
        cumulative_volume: float = 0.0,
        operating_hours: float = 0.0,
        previous_health: List = None,
        maintenance_events: List = None,
    ) -> "FilterHealthIndex":
        """
        Compute Filter Health Index from stress and lifecycle data.
        
        Args:
            filter_stress: Current Filter Stress Index
            filter_install_date: When filter was installed
            cumulative_volume: Total water processed (L)
            operating_hours: Total pump operating hours
            previous_health: Historical health indices for trend
            maintenance_events: Maintenance history
            
        Returns:
            FilterHealthIndex with health score and state
        """
        config = self.config
        
        # Component scores (0-100, higher = better health)
        components = {}
        
        # 1. Stress component (inverted: lower stress = better health)
        stress_score = max(0, 100 - filter_stress.score)
        components['stress'] = stress_score
        
        # 2. Lifecycle component (age-based)
        lifecycle_score = self._score_lifecycle(filter_install_date)
        components['lifecycle'] = lifecycle_score
        
        # 3. Usage component (volume-based)
        usage_score = self._score_usage(cumulative_volume)
        components['usage'] = usage_score
        
        # 4. Pressure/Flow behavior component
        pf_score = self._score_pressure_flow_behavior()
        components['pressure_flow'] = pf_score
        
        # 5. Historical behavior component (trend from previous health)
        historical_score = self._score_historical_behavior(previous_health)
        components['historical'] = historical_score
        
        # Calculate weighted total
        weights = {
            'stress': config.stress_weight,
            'lifecycle': config.lifecycle_weight,
            'usage': config.usage_weight,
            'pressure_flow': config.pressure_flow_weight,
            'historical': config.historical_behavior_weight,
        }
        
        weighted_sum = sum(
            components.get(k, 0) * weights.get(k, 0) 
            for k in components
        )
        total_weight = sum(weights.get(k, 0) for k in components)
        
        overall_score = (weighted_sum / total_weight) if total_weight > 0 else 0
        overall_score = max(0, min(100, int(round(overall_score))))
        
        # Determine state
        if overall_score >= config.excellent_min:
            state = FilterHealthState.EXCELLENT
        elif overall_score >= config.good_min:
            state = FilterHealthState.GOOD
        elif overall_score >= config.fair_min:
            state = FilterHealthState.FAIR
        elif overall_score >= config.poor_min:
            state = FilterHealthState.POOR
        else:
            state = FilterHealthState.CRITICAL
        
        # Confidence based on data availability
        confidence = self._calculate_confidence(
            filter_stress, filter_install_date, previous_health
        )
        
        # Contributing factors
        factors = self._build_factors(components)
        
        return FilterHealthIndex(
            device_id=UUID(int=0),  # Will be set by caller
            timestamp=datetime.utcnow(),
            health_score=overall_score,
            state=state,
            confidence=round(confidence, 2),
            contributing_factors=factors,
            evidence=self._build_evidence(filter_stress, components),
            calculation_version="1.0",
            stress_component=components.get('stress'),
            lifecycle_component=components.get('lifecycle'),
            usage_component=components.get('usage'),
            pressure_flow_component=components.get('pressure_flow'),
            historical_behavior_component=components.get('historical'),
        )
    
    def _score_lifecycle(self, install_date: datetime) -> float:
        """Score based on filter age (0-100, higher = better)."""
        if install_date is None:
            return 50.0  # Unknown = neutral
        
        age_days = (datetime.utcnow() - install_date).days
        # Assume 365 days = end of life
        if age_days <= 0:
            return 100.0
        elif age_days >= 365:
            return 0.0
        else:
            return max(0, 100 - (age_days / 365) * 100)
    
    def _score_usage(self, volume: float) -> float:
        """Score based on cumulative volume (0-100, higher = better)."""
        # Assume 10,000 L = end of life
        if volume <= 0:
            return 100.0
        elif volume >= 10000:
            return 0.0
        else:
            return max(0, 100 - (volume / 10000) * 100)
    
    def _score_pressure_flow_behavior(self) -> float:
        """Score based on pressure/flow stability.
        In production, this would analyze pressure/flow stability over time.
        """
        # Simplified - would use hydraulic intelligence in production
        return 75.0
    
    def _score_historical_behavior(self, previous_health: List) -> float:
        """Score based on health trend from previous readings."""
        if not previous_health or len(previous_health) < 2:
            return 75.0  # Neutral
        
        # Check trend
        recent_scores = [h.health_score for h in previous_health[-5:] if hasattr(h, 'health_score')]
        if len(recent_scores) < 2:
            return 75.0
        
        # If health is declining, reduce score
        trend = recent_scores[-1] - recent_scores[0]
        if trend < -10:
            return 50.0
        elif trend < 0:
            return 65.0
        elif trend > 10:
            return 90.0
        else:
            return 75.0
    
    def _calculate_confidence(
        self, 
        filter_stress, 
        install_date: datetime, 
        previous_health: List
    ) -> float:
        """Calculate confidence (0-1) based on data availability."""
        score = 0.0
        
        if filter_stress:
            score += 0.3
        if install_date:
            score += 0.3
        if previous_health and len(previous_health) >= 5:
            score += 0.4
        elif previous_health:
            score += 0.2
        
        return min(1.0, score)
    
    def _build_factors(self, components: Dict) -> List[str]:
        """Build human-readable factor list."""
        factors = []
        
        if components.get('stress', 100) < 50:
            factors.append("high_filter_stress")
        if components.get('lifecycle', 100) < 50:
            factors.append("advanced_filter_age")
        if components.get('usage', 100) < 50:
            factors.append("high_cumulative_usage")
        if components.get('pressure_flow', 100) < 70:
            factors.append("unstable_pressure_flow")
        if components.get('historical', 75) < 60:
            factors.append("declining_health_trend")
        
        return factors
    
    def _build_evidence(self, filter_stress, components) -> Dict:
        return {
            "filter_stress_score": filter_stress.score if filter_stress else None,
            "filter_stress_state": filter_stress.state.value if filter_stress else None,
            "component_scores": components,
            "weights": {
                "stress": 0.30,
                "lifecycle": 0.25,
                "usage": 0.20,
                "pressure_flow": 0.15,
                "historical": 0.10,
            },
        }