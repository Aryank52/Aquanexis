"""
Water Quality service - computes AquaScore, trends, anomalies.
"""
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from uuid import UUID

from app.domain.water_quality import (
    AquaScore,
    ParameterScore,
    TrendAnalysis,
    AnomalyFlag,
    TrendDirection,
    AnomalyType,
    GUIDELINES,
    PARAMETER_WEIGHTS,
    score_parameter,
    compute_aquascore,
    compute_trends,
    detect_anomalies,
)
from app.domain.readings import SensorReading
from app.domain.water_quality import AquaScore as DomainAquaScore


class WaterQualityService:
    """Service for computing water quality metrics."""

    def __init__(self):
        self.parameter_weights = PARAMETER_WEIGHTS.copy()
        self.guidelines = {k: v.copy() for k, v in GUIDELINES.items()}

    def compute_aquascore(
        self,
        reading,
        parameter_scores: Optional[List[ParameterScore]] = None,
        device_config: Optional[Dict] = None,
    ) -> DomainAquaScore:
        """
        Compute AquaScore from a single reading.
        
        Args:
            reading: SensorReading or SensorReadingModel
            parameter_scores: Pre-computed parameter scores (optional)
            device_config: Device configuration for custom weights
            
        Returns:
            Domain AquaScore object
        """
        if parameter_scores is None:
            parameter_scores = self._compute_parameter_scores(reading)
        
        # Use device-specific weights if provided
        weights = self.parameter_weights.copy()
        if device_config and "aquascore_weights" in device_config:
            weights.update(device_config["aquascore_weights"])
        
        total_weight = 0
        weighted_sum = 0
        
        for param_score in parameter_scores:
            weight = weights.get(param_score.parameter, 0)
            if weight > 0:
                weighted_sum += param_score.score * weight
                total_weight += weight
        
        overall_score = int(weighted_sum / total_weight) if total_weight > 0 else 0
        
        # Determine state
        if overall_score >= 90:
            state = "EXCELLENT"
        elif overall_score >= 70:
            state = "GOOD"
        elif overall_score >= 50:
            state = "FAIR"
        else:
            state = "POOR"
        
        # Calculate confidence based on data quality
        confidence = self._calculate_confidence(reading)
        
        # Get contributors
        contributors = self._get_contributors(parameter_scores, weights)
        
        # Data quality
        data_quality = self._assess_data_quality(reading)
        
        return DomainAquaScore(
            device_id=getattr(reading, 'device_id', UUID(int=0)),
            timestamp=getattr(reading, 'timestamp', datetime.utcnow()),
            overall_score=overall_score,
            parameter_scores=parameter_scores,
            trends=[],  # Will be filled by caller
            anomaly_score=0.0,
            anomaly_flags=[],
        )
    
    def _compute_parameter_scores(self, reading) -> List:
        """Compute scores for all available parameters."""
        from app.domain.water_quality import score_parameter
        
        parameter_scores = []
        for param, weight in self.parameter_weights.items():
            value = getattr(reading, param, None)
            if value is not None:
                param_score = score_parameter(param, value)
                parameter_scores.append(param_score)
        return parameter_scores
    
    def _calculate_confidence(self, reading) -> float:
        """Calculate confidence based on data quality."""
        # Simplified: based on how many parameters are available
        available = sum(1 for param in self.parameter_weights if getattr(reading, param, None) is not None)
        total = len(self.parameter_weights)
        return available / total if total > 0 else 0.0
    
    def _get_contributors(self, parameter_scores: List, weights: Dict) -> List[Dict]:
        """Get contributing signals with their contribution."""
        contributors = []
        for ps in parameter_scores:
            weight = weights.get(ps.parameter, 0)
            if weight > 0 and ps.value is not None:
                contribution = ps.score * weight
                contributors.append({
                    "parameter": ps.parameter,
                    "value": ps.value,
                    "unit": ps.unit,
                    "score": ps.score,
                    "weight": weight,
                    "contribution": contribution,
                    "status": ps.status,
                })
        # Sort by contribution descending
        contributors.sort(key=lambda x: x["contribution"], reverse=True)
        return contributors
    
    def _assess_data_quality(self, reading) -> str:
        """Assess overall data quality."""
        available = sum(1 for param in self.parameter_weights if getattr(reading, param, None) is not None)
        total = len(self.parameter_weights)
        ratio = available / total if total > 0 else 0
        if ratio >= 0.8:
            return "HIGH"
        elif ratio >= 0.5:
            return "MEDIUM"
        return "LOW"
    
    def compute_trends(
        self,
        readings_history: List,
        windows: List[str] = None,
        parameters: List[str] = None,
    ) -> List:
        """Compute trend analysis for multiple time windows."""
        from app.domain.water_quality import compute_trends
        return compute_trends(readings_history, windows, parameters)
    
    def detect_anomalies(
        self,
        readings_window: List,
        parameters: List[str] = None,
        zscore_threshold: float = 3.0,
        iqr_multiplier: float = 1.5,
    ) -> List:
        """Detect anomalies using statistical methods."""
        from app.domain.water_quality import detect_anomalies
        return detect_anomalies(readings_window, parameters, zscore_threshold, iqr_multiplier)
    
    def get_aquascore_explanation(
        self,
        aquascore,
        parameter_scores: List,
        weights: Dict = None,
    ) -> Dict:
        """Generate human-readable explanation for AquaScore."""
        weights = weights or self.parameter_weights
        contributors = self._get_contributors(aquascore.parameter_scores, weights)
        
        # Determine state
        if aquascore.overall_score >= 90:
            state = "EXCELLENT"
        elif aquascore.overall_score >= 70:
            state = "GOOD"
        elif aquascore.overall_score >= 50:
            state = "FAIR"
        else:
            state = "POOR"
        
        # Data quality
        available = len([ps for ps in parameter_scores if ps.value is not None])
        total = len(self.parameter_weights)
        data_quality = "HIGH" if available / max(total, 1) >= 0.8 else ("MEDIUM" if available / max(total, 1) >= 0.5 else "LOW")
        
        # Excluded signals (parameters with no data)
        excluded = [param for param in self.parameter_weights if not any(ps.parameter == param for ps in parameter_scores)]
        
        return {
            "overall_score": aquascore.overall_score,
            "state": state,
            "confidence": aquascore.confidence if hasattr(aquascore, 'confidence') else 0.8,
            "contributors": contributors,
            "excluded_signals": excluded,
            "data_quality": data_quality,
            "calculation_version": "1.0",
        }