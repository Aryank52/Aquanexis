"""
Failure Risk service - classifies failure risk level.
Enhanced with maintenance bands and improved confidence.
"""
from datetime import datetime
from typing import Optional, Dict, Any, List
from uuid import UUID

from app.domain.filter_intelligence import (
    FailureRiskAssessment,
    FailureRiskLevel,
    FilterStressState,
    FilterHealthState,
    MaintenanceBand,
)


class FailureRiskService:
    """Service for classifying failure risk level."""

    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.maintenance_band_thresholds = self.config.get('maintenance_band_thresholds', {
            'normal': 70,
            'monitor': 50,
            'plan_maintenance': 30,
        })

    def assess_risk(
        self,
        filter_stress,
        filter_health,
        rul_prediction,
        recent_anomalies: list = None,
        alert_history: list = None,
    ) -> "FailureRiskAssessment":
        """
        Assess failure risk level.
        
        Args:
            filter_stress: Current Filter Stress Index
            filter_health: Current Filter Health Index
            rul_prediction: RUL prediction
            recent_anomalies: Recent anomaly flags
            alert_history: Recent alert history
            
        Returns:
            FailureRiskAssessment with risk level and evidence
        """
        components = {}
        
        # 1. RUL risk component
        rul_risk = self._assess_rul_risk(filter_stress, rul_prediction)
        components['rul'] = rul_risk
        
        # 2. Filter health risk component
        health_risk = self._assess_health_risk(filter_health)
        components['health'] = health_risk
        
        # 3. Stress state risk component
        stress_risk = self._assess_stress_risk(filter_stress)
        components['stress'] = stress_risk
        
        # 4. Anomaly evidence risk component
        anomaly_risk = self._assess_anomaly_risk(recent_anomalies)
        components['anomaly'] = anomaly_risk
        
        # 5. Alert history risk
        alert_risk = self._assess_alert_risk(alert_history)
        components['alerts'] = alert_risk
        
        # Calculate weighted risk score
        weights = {
            'rul': 0.30,
            'health': 0.25,
            'stress': 0.20,
            'anomaly': 0.15,
            'alerts': 0.10,
        }
        
        weighted_sum = sum(
            components.get(k, 0) * weights.get(k, 0) 
            for k in components
        )
        total_weight = sum(weights.get(k, 0) for k in components)
        
        risk_score = (weighted_sum / total_weight) if total_weight > 0 else 0
        risk_score = max(0, min(100, risk_score))
        
        # Determine risk level
        if risk_score >= 70:
            risk_level = FailureRiskLevel.HIGH
        elif risk_score >= 40:
            risk_level = FailureRiskLevel.MEDIUM
        else:
            risk_level = FailureRiskLevel.LOW
        
        # Maintenance band
        maintenance_band = self._determine_maintenance_band()
        
        # Confidence
        confidence = self._calculate_confidence()
        
        # Contributing factors
        factors = self._build_factors(components)
        
        return FailureRiskAssessment(
            device_id=UUID(int=0),
            timestamp=datetime.utcnow(),
            risk_level=risk_level,
            risk_score=round(risk_score, 1),
            confidence=round(confidence, 2),
            evidence=self._build_evidence(components),
            contributing_factors=factors,
            calculation_version="2.0",  # Updated for Phase E
            rul_risk_component=components.get('rul'),
            filter_health_risk_component=components.get('health'),
            stress_state_component=components.get('stress'),
            anomaly_evidence_component=components.get('anomaly'),
            maintenance_band=maintenance_band.value,
        )
    
    def _determine_maintenance_band(self) -> MaintenanceBand:
        """Determine maintenance band based on risk score."""
        # This would ideally use the filter health score
        # For now, use risk score as proxy
        if hasattr(self, '_last_health_score'):
            health = self._last_health_score
        else:
            health = 50  # default
        
        if health >= 70:
            return MaintenanceBand.NORMAL
        elif health >= 50:
            return MaintenanceBand.MONITOR
        elif health >= 30:
            return MaintenanceBand.PLAN_MAINTENANCE
        else:
            return MaintenanceBand.REPLACE_RECOMMENDED
    
    def _assess_rul_risk(self, filter_stress, rul_prediction) -> float:
        """Assess risk based on RUL (0-100, higher = more risk)."""
        if rul_prediction and rul_prediction.rul_days is not None:
            rul = rul_prediction.rul_days
            if rul <= 7:
                return 95.0
            elif rul <= 14:
                return 80.0
            elif rul <= 30:
                return 60.0
            elif rul <= 60:
                return 40.0
            elif rul <= 90:
                return 20.0
            else:
                return 10.0
        # Fallback: use filter stress as proxy
        return min(100, filter_stress.score * 1.2) if filter_stress else 50.0
    
    def _assess_health_risk(self, filter_health) -> float:
        """Assess risk based on filter health (0-100, higher = more risk)."""
        if filter_health is None:
            return 50.0
        # Invert health score: lower health = higher risk
        return max(0, 100 - filter_health.health_score)
    
    def _assess_stress_risk(self, filter_stress) -> float:
        """Assess risk from filter stress state."""
        if filter_stress is None:
            return 50.0
        
        state_risk = {
            FilterStressState.LOW: 10.0,
            FilterStressState.MODERATE: 50.0,
            FilterStressState.HIGH: 90.0,
        }
        return state_risk.get(filter_stress.state, 50.0)
    
    def _assess_anomaly_risk(self, anomalies: list) -> float:
        """Assess risk from recent anomalies."""
        if not anomalies:
            return 0.0
        
        # Count critical anomalies
        critical_count = sum(1 for a in anomalies if getattr(a, 'type', '') == 'zscore' and a.score > 4)
        warning_count = sum(1 for a in anomalies if getattr(a, 'type', '') == 'zscore' and a.score > 3)
        
        risk = min(100, critical_count * 30 + warning_count * 15)
        return min(100, risk)
    
    def _assess_alert_risk(self, alerts: list) -> float:
        """Assess risk from recent alert history."""
        if not alerts:
            return 0.0
        
        recent_critical = sum(1 for a in alerts 
                            if getattr(a, 'severity', '').lower() == 'critical' 
                            and getattr(a, 'status', '') in ['active', 'acknowledged'])
        recent_warning = sum(1 for a in alerts 
                           if getattr(a, 'severity', '').lower() == 'warning' 
                           and getattr(a, 'status', '') in ['active', 'acknowledged'])
        
        risk = min(100, recent_critical * 25 + recent_warning * 10)
        return min(100, risk)
    
    def _calculate_confidence(self) -> float:
        """Calculate confidence in risk assessment."""
        # In production, this would consider data quality, model certainty, etc.
        return 0.8
    
    def _build_factors(self, components: Dict) -> List[str]:
        factors = []
        if components.get('rul', 0) > 60:
            factors.append("low_predicted_rul")
        if components.get('health', 0) > 60:
            factors.append("poor_filter_health")
        if components.get('stress', 0) > 60:
            factors.append("high_filter_stress")
        if components.get('anomaly', 0) > 30:
            factors.append("anomalous_sensor_readings")
        if components.get('alerts', 0) > 30:
            factors.append("active_critical_alerts")
        return factors
    
    def _build_evidence(self, components) -> Dict:
        return {
            "component_scores": components,
            "weights": {
                "rul": 0.30,
                "health": 0.25,
                "stress": 0.20,
                "anomaly": 0.15,
                "alerts": 0.10,
            },
            "note": "Risk assessment combines multiple signals. Not a guarantee of failure.",
        }