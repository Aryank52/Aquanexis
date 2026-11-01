"""
RUL (Remaining Useful Life) service - ML-based prediction with fallback.
"""
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from uuid import UUID
import pickle
import os

from app.domain.filter_intelligence import (
    RULPrediction,
    PredictionStatus,
    RULConfig,
    DEFAULT_RUL_CONFIG,
)


class RULService:
    """Service for Remaining Useful Life prediction."""

    def __init__(self, config: RULConfig = None):
        self.config = config or DEFAULT_RUL_CONFIG
        self._model = None
        self._model_metadata = {}
        self._last_inference = None

    def load_model(self, model_path: str = None) -> bool:
        """Load ML model from disk."""
        path = model_path or self.config.model_path
        if not os.path.exists(path):
            return False
        
        try:
            with open(path, 'rb') as f:
                model_data = pickle.load(f)
                self._model = model_data.get('model')
                self._model_metadata = {
                    'model_name': model_data.get('model_name', 'unknown'),
                    'model_version': model_data.get('model_version', 'unknown'),
                    'dataset_version': model_data.get('dataset_version', 'unknown'),
                    'feature_names': model_data.get('feature_names', []),
                    'metrics': model_data.get('metrics', {}),
                    'trained_at': model_data.get('trained_at'),
                }
                return True
        except Exception as e:
            return False

    def predict_rul(
        self,
        filter_stress,
        filter_health,
        hydraulic_intelligence,
        purification_performance,
        device_features: Dict = None,
    ) -> "RULPrediction":
        """Predict Remaining Useful Life."""
        if self._model is None:
            self.load_model()
        
        if self._model is None:
            return self._fallback_prediction(
                reason="model_missing",
                status=PredictionStatus.MODEL_MISSING,
            )
        
        if (self._last_inference and 
            datetime.utcnow() - self._last_inference < timedelta(minutes=self.config.inference_cadence_minutes)):
            pass
        
        features = self._prepare_features(
            filter_stress, filter_health, hydraulic_intelligence, 
            purification_performance, device_features
        )
        
        if not features:
            return self._fallback_prediction(
                reason="insufficient_features",
                status=PredictionStatus.INSUFFICIENT_DATA,
            )
        
        try:
            rul_days = self._model.predict([list(features.values())])[0]
            rul_days = max(0, float(rul_days))
            
            confidence = self._get_confidence(features)
            
            if self._model_metadata.get('metrics', {}).get('mae'):
                mae = self._model_metadata['metrics']['mae']
                confidence_lower = max(0, rul_days - 1.96 * mae)
                confidence_upper = rul_days + 1.96 * mae
            else:
                confidence_lower = max(0, rul_days * 0.7)
                confidence_upper = rul_days * 1.3
            
            if confidence < self.config.confidence_threshold:
                return self._fallback_prediction(
                    reason="low_confidence",
                    status=PredictionStatus.UNAVAILABLE,
                    rul_days=rul_days,
                    confidence=confidence,
                )
            
            importance = self._get_feature_importance()
            explanation = self._generate_explanation(features, rul_days, confidence)
            
            self._last_inference = datetime.utcnow()
            
            return RULPrediction(
                device_id=UUID(int=0),
                timestamp=datetime.utcnow(),
                rul_days=round(rul_days, 1),
                confidence_lower=round(confidence_lower, 1),
                confidence_upper=round(confidence_upper, 1),
                status=PredictionStatus.AVAILABLE,
                model_name=self._model_metadata.get('model_name', 'unknown'),
                model_version=self._model_metadata.get('model_version', 'unknown'),
                dataset_version=self._model_metadata.get('dataset_version', 'unknown'),
                input_features=features,
                explanation=self._format_explanation(explanation),
                feature_importance=importance,
            )
            
        except Exception as e:
            return self._fallback_prediction(
                reason=f"inference_error: {str(e)}",
                status=PredictionStatus.UNAVAILABLE,
            )
    
    def _fallback_prediction(
        self,
        reason: str,
        status: "PredictionStatus",
        rul_days: float = None,
        confidence: float = None,
    ) -> "RULPrediction":
        return RULPrediction(
            device_id=UUID(int=0),
            timestamp=datetime.utcnow(),
            rul_days=rul_days,
            status=status,
            model_name="fallback",
            model_version="1.0",
            input_features={},
            explanation={"reason": reason, "fallback": True},
            feature_importance={},
        )
    
    def _prepare_features(
        self,
        filter_stress,
        filter_health,
        hydraulic_intelligence,
        purification_performance,
        device_features: Dict = None,
    ) -> Dict[str, float]:
        features = {}
        
        if filter_stress:
            features['fsi_score'] = filter_stress.score
            features['fsi_state'] = {'low': 0, 'moderate': 1, 'high': 2}.get(
                filter_stress.state.value, 0
            )
            features['dp_score'] = filter_stress.differential_pressure_score or 0
            features['flow_dev_score'] = filter_stress.flow_deviation_score or 0
            features['turbidity_score'] = filter_stress.turbidity_exposure_score or 0
            features['cum_vol_score'] = filter_stress.cumulative_volume_score or 0
            features['age_score'] = filter_stress.filter_age_score or 0
            features['op_hours_score'] = filter_stress.operating_hours_score or 0
            features['tds_trend_score'] = filter_stress.tds_trend_score or 0
        
        if device_features:
            features.update(device_features)
        
        if hydraulic_intelligence:
            features['dp'] = hydraulic_intelligence.differential_pressure or 0
            features['flow_dev'] = hydraulic_intelligence.flow_deviation_pct or 0
            features['pressure_trend'] = hydraulic_intelligence.pressure_trend or 0
            features['flow_trend'] = hydraulic_intelligence.flow_trend or 0
        
        if purification_performance:
            features['rejection_rate'] = purification_performance.rejection_rate or 0
            features['recovery'] = purification_performance.recovery_ratio or 0
        
        return features
    
    def _get_confidence(self, features: Dict) -> float:
        return 0.85
    
    def _get_feature_importance(self) -> Dict[str, float]:
        if hasattr(self._model, 'feature_importances_'):
            names = self._model_metadata.get('feature_names', [])
            importances = self._model.feature_importances_
            return dict(zip(names, importances.tolist()))
        return {}
    
    def _generate_explanation(
        self,
        features: Dict,
        rul_days: float,
        confidence: float,
    ) -> Dict:
        factors = []
        
        if features.get('fsi_score', 0) > 70:
            factors.append("High Filter Stress Index indicates accelerated degradation")
        if features.get('dp', 0) > 150:
            factors.append("High differential pressure indicates fouling")
        if features.get('tds_trend', 0) > 0.5:
            factors.append("Rising TDS trend indicates membrane degradation")
        
        return {
            "summary": f"Estimated {rul_days:.1f} days remaining",
            "confidence": f"{confidence:.0%}",
            "top_factors": factors[:3],
            "model_version": "1.0",
        }
    
    def _format_explanation(self, explanation: Dict) -> Dict:
        return {
            "summary": explanation.get("summary", ""),
            "confidence": explanation.get("confidence", ""),
            "top_factors": explanation.get("top_factors", []),
            "model_version": explanation.get("model_version", ""),
            "note": "Prediction based on ML model with deterministic fallback. Not a guarantee of actual filter life.",
        }
    
    def _fallback_prediction(
        self,
        reason: str,
        status: "PredictionStatus",
        rul_days: float = None,
        confidence: float = None,
    ) -> "RULPrediction":
        return RULPrediction(
            device_id=UUID(int=0),
            timestamp=datetime.utcnow(),
            rul_days=rul_days,
            status=status,
            model_name="fallback",
            model_version="1.0",
            input_features={},
            explanation={"reason": reason, "fallback": True},
            feature_importance={},
        )