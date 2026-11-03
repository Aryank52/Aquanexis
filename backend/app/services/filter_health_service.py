"""
Filter Health service - computes Filter Health Index from stress and lifecycle.
Enhanced with maintenance bands, counterfactual analysis, hydraulic integration.
"""

from datetime import datetime
from typing import Dict, List, Optional
from uuid import UUID

from app.domain.filter_intelligence import (
    DEFAULT_FILTER_HEALTH_CONFIG,
    CounterfactualAnalysis,
    FilterHealthConfig,
    FilterHealthIndex,
    FilterHealthState,
    FilterStressIndex,
    HydraulicIntelligence,
    MaintenanceBand,
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
        hydraulic_intelligence: HydraulicIntelligence = None,
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
            hydraulic_intelligence: Hydraulic intelligence for pressure/flow analysis

        Returns:
            FilterHealthIndex with health score and state
        """
        config = self.config

        # Component scores (0-100, higher = better health)
        components = {}

        # 1. Stress component (inverted: lower stress = better health)
        stress_score = max(0, 100 - filter_stress.score)
        components["stress"] = stress_score

        # 2. Lifecycle component (age-based) - only if install date recorded
        lifecycle_score = self._score_lifecycle(filter_install_date)
        if lifecycle_score is not None:
            components["lifecycle"] = lifecycle_score

        # 3. Usage component (volume-based) - only if volume recorded
        usage_score = self._score_usage(cumulative_volume)
        if usage_score is not None:
            components["usage"] = usage_score

        # 4. Pressure/Flow behavior component - only if hydraulic data measured
        pf_score = self._score_pressure_flow_behavior(hydraulic_intelligence)
        if pf_score is not None:
            components["pressure_flow"] = pf_score

        # 5. Historical behavior component - only if previous health history exists
        historical_score = self._score_historical_behavior(previous_health)
        if historical_score is not None:
            components["historical"] = historical_score

        # Calculate weighted total dynamically based on available components
        weights = {
            "stress": config.stress_weight,
            "lifecycle": config.lifecycle_weight,
            "usage": config.usage_weight,
            "pressure_flow": config.pressure_flow_weight,
            "historical": config.historical_behavior_weight,
        }

        active_weights = {k: weights[k] for k in components if components[k] is not None}
        weighted_sum = sum(components[k] * active_weights[k] for k in active_weights)
        total_weight = sum(active_weights.values())

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

        # Maintenance band determination
        maintenance_band = self._determine_maintenance_band(overall_score)

        # Confidence based on data availability
        confidence = self._calculate_confidence(filter_stress, filter_install_date, previous_health)

        # Contributing factors
        factors = self._build_factors(components)

        # Counterfactual analysis
        counterfactual = self._generate_counterfactual(filter_stress, previous_health)

        return FilterHealthIndex(
            device_id=UUID(int=0),  # Will be set by caller
            timestamp=datetime.utcnow(),
            health_score=overall_score,
            state=state,
            confidence=round(confidence, 2),
            contributing_factors=factors,
            evidence=self._build_evidence(filter_stress, components),
            calculation_version="2.0",  # Updated for Phase E
            stress_component=components.get("stress"),
            lifecycle_component=components.get("lifecycle"),
            usage_component=components.get("usage"),
            pressure_flow_component=components.get("pressure_flow"),
            historical_behavior_component=components.get("historical"),
            maintenance_band=maintenance_band.value,
            counterfactual=previous_health and counterfactual or None,
        )

    def _determine_maintenance_band(self, health_score: int) -> MaintenanceBand:
        """Determine maintenance band based on health score."""
        if health_score >= self.config.excellent_min:
            return MaintenanceBand.NORMAL
        elif health_score >= self.config.monitor_min:
            return MaintenanceBand.MONITOR
        elif health_score >= self.config.plan_maintenance_min:
            return MaintenanceBand.PLAN_MAINTENANCE
        else:
            return MaintenanceBand.REPLACE_RECOMMENDED

    def _score_lifecycle(self, install_date: datetime) -> Optional[float]:
        """Score based on filter age (0-100, higher = better)."""
        if install_date is None:
            return None  # Excluded from denominator when not installed / recorded

        age_days = (datetime.utcnow() - install_date).days
        # Assume 365 days = rated service life
        if age_days <= 0:
            return 100.0
        elif age_days >= 365:
            return 0.0
        else:
            return max(0.0, 100.0 - (age_days / 365.0) * 100.0)

    def _score_usage(self, volume: float) -> Optional[float]:
        """Score based on cumulative volume (0-100, higher = better)."""
        if volume is None:
            return None
        # Assume 10,000 L = rated volume life
        if volume <= 0:
            return 100.0
        elif volume >= 10000:
            return 0.0
        else:
            return max(0.0, 100.0 - (volume / 10000.0) * 100.0)

    def _score_pressure_flow_behavior(
        self, hydraulic: HydraulicIntelligence = None
    ) -> Optional[float]:
        """Score based on pressure/flow stability."""
        if hydraulic and hydraulic.pressure_stability is not None:
            stability = hydraulic.pressure_stability
            if stability < 5:
                return 95.0
            elif stability < 10:
                return 80.0
            elif stability < 20:
                return 60.0
            else:
                return 40.0
        return None  # Excluded from denominator if unmeasured

    def _score_historical_behavior(self, previous_health: List) -> Optional[float]:
        """Score based on health trend from previous readings."""
        if not previous_health or len(previous_health) < 2:
            return None  # Excluded until history is established

        # Check trend
        recent_scores = [h.health_score for h in previous_health[-5:] if hasattr(h, "health_score")]
        if len(recent_scores) < 2:
            return None

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
        self, filter_stress, install_date: datetime, previous_health: List
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

        if components.get("stress", 100) < 50:
            factors.append("high_filter_stress")
        if components.get("lifecycle", 100) < 50:
            factors.append("advanced_filter_age")
        if components.get("usage", 100) < 50:
            factors.append("high_cumulative_usage")
        if components.get("pressure_flow", 100) < 70:
            factors.append("unstable_pressure_flow")
        if components.get("historical", 75) < 60:
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

    def _generate_counterfactual(
        self, filter_stress, previous_health: List
    ) -> CounterfactualAnalysis:
        """Generate what-changed analysis if we have previous health."""
        if not previous_health or len(previous_health) < 2:
            return CounterfactualAnalysis(
                device_id=UUID(int=0),
                timestamp=datetime.utcnow(),
                narrative="Insufficient history for counterfactual analysis",
            )

        current_health = previous_health[-1].health_score if previous_health else 0
        previous_health_score = (
            previous_health[-2].health_score if len(previous_health) >= 2 else current_health
        )

        current_fsi = filter_stress.score if filter_stress else 0
        previous_fsi = (
            previous_health[-2].fsi
            if len(previous_health) >= 2
            else filter_stress.score
            if filter_stress
            else 0
        )

        health_change = current_health - previous_health_score
        fsi_change = current_fsi - previous_fsi

        changes = []
        if abs(fsi_change) > 5:
            direction = "increased" if fsi_change > 0 else "decreased"
            changes.append(
                {
                    "feature": "fsi",
                    "previous": previous_fsi,
                    "current": current_fsi,
                    "change": fsi_change,
                    "direction": direction,
                }
            )

        # Build narrative
        factors = []
        if fsi_change > 5:
            factors.append("FSI increased significantly")
        elif fsi_change < -5:
            factors.append("FSI decreased significantly")

        if current_health < previous_health_score:
            factors.append("Health score declining")
        elif current_health > previous_health_score:
            factors.append("Health score improving")

        narrative = (
            "RUL changed from {} to {} days. ".format(previous_health_score, current_health)
            + "; ".join(factors)
            if factors
            else "No significant changes detected."
        )

        return CounterfactualAnalysis(
            device_id=UUID(int=0),
            timestamp=datetime.utcnow(),
            previous_rul_days=previous_health_score,
            current_rul_days=current_health,
            rul_change_days=current_health - previous_health_score,
            rul_change_pct=(
                (current_health - previous_health_score) / max(previous_health_score, 1)
            )
            * 100
            if previous_health_score
            else None,
            contributing_changes=changes,
            narrative=narrative,
        )
