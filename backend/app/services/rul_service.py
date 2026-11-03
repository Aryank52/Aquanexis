"""
RUL (Remaining Useful Life) service - ML-based prediction with fallback.
Enhanced with model registry, prediction stability, confidence levels, and counterfactual analysis.
"""

import os
import pickle
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
from uuid import UUID

from app.domain.filter_intelligence import (
    DEFAULT_RUL_CONFIG,
    CounterfactualAnalysis,
    DatasetMetadata,
    ExperimentRecord,
    PredictionStatus,
    RULConfig,
    RULPrediction,
    RULStabilityReport,
)


class RULService:
    """Service for Remaining Useful Life prediction."""

    def __init__(self, config: RULConfig = None):
        self.config = config or DEFAULT_RUL_CONFIG
        self._model = None
        self._model_metadata = {}
        self._last_inference = None
        self._prediction_history: List[Tuple[datetime, float]] = []  # (timestamp, rul_days)

    def load_model(self, model_path: str = None) -> bool:
        """Load ML model from disk."""
        candidates = [
            model_path,
            os.getenv("RUL_MODEL_PATH"),
            getattr(self.config, "model_path", None),
            os.path.join(os.path.dirname(__file__), "..", "models", "rul_model.pkl"),
            os.path.join(os.getcwd(), "app", "models", "rul_model.pkl"),
        ]
        target_path = None
        for p in candidates:
            if p and os.path.exists(p):
                target_path = p
                break

        if not target_path:
            return False

        try:
            with open(target_path, "rb") as f:
                model_data = pickle.load(f)
                self._model = model_data.get("model")
                self._model_metadata = {
                    "model_name": model_data.get("model_name", "unknown"),
                    "model_version": model_data.get("model_version", "unknown"),
                    "dataset_version": model_data.get("dataset_version", "unknown"),
                    "feature_names": model_data.get("feature_names", []),
                    "metrics": model_data.get("metrics", {}),
                    "trained_at": model_data.get("trained_at"),
                }
                return True
        except Exception:
            return False

    def predict_rul(
        self,
        filter_stress,
        filter_health,
        hydraulic_intelligence,
        purification_performance,
        device_features: Dict = None,
        previous_rul: float = None,
    ) -> "RULPrediction":
        """Predict Remaining Useful Life."""
        if self._model is None:
            self.load_model()

        if self._model is None:
            return self._fallback_prediction(
                reason="model_missing",
                status=PredictionStatus.MODEL_MISSING,
            )

        if self._last_inference and datetime.utcnow() - self._last_inference < timedelta(
            minutes=self.config.inference_cadence_minutes
        ):
            pass

        features = self._prepare_features(
            filter_stress,
            filter_health,
            hydraulic_intelligence,
            purification_performance,
            device_features,
        )

        if not features:
            return self._fallback_prediction(
                reason="insufficient_features",
                status=PredictionStatus.INSUFFICIENT_DATA,
            )

        try:
            pred_res = (
                self._model.predict([features]) if hasattr(self._model, "predict") else [features]
            )
            rul_days = max(0.0, float(pred_res[0]))

            # Check prediction stability
            is_stable, stability_reason = self._check_stability(rul_days)

            confidence = self._get_confidence(features)

            if self._model_metadata.get("metrics", {}).get("mae"):
                mae = self._model_metadata["metrics"]["mae"]
                confidence_lower = max(0, rul_days - 1.96 * mae)
                confidence_upper = rul_days + 1.96 * mae
            else:
                confidence_lower = max(0, rul_days * 0.7)
                confidence_upper = rul_days * 1.3

            if confidence < self.config.confidence_threshold:
                return self._fallback_prediction(
                    reason="low_confidence",
                    status=PredictionStatus.LOW_CONFIDENCE,
                    rul_days=rul_days,
                    confidence=confidence,
                )

            importance = self._get_feature_importance()
            explanation = self._generate_explanation(features, rul_days, confidence)

            # Counterfactual analysis
            counterfactual = None
            if self._prediction_history:
                counterfactual = self._generate_counterfactual(previous_rul)

            # Determine confidence level
            if confidence >= 0.8:
                confidence_level = "high"
            elif confidence >= 0.6:
                confidence_level = "medium"
            else:
                confidence_level = "low"

            # Check stability
            is_stable = True
            if previous_rul is not None:
                rul_change_pct = abs(rul_days - previous_rul) / max(previous_rul, 1) * 100
                if rul_change_pct > self.config.rul_max_change_per_window_pct:
                    is_stable = False

            self._last_inference = datetime.utcnow()
            self._prediction_history.append((datetime.utcnow(), rul_days))
            # Keep only last window
            cutoff = datetime.utcnow() - timedelta(hours=self.config.rul_stability_window_hours)
            self._prediction_history = [
                (ts, rul) for ts, rul in self._prediction_history if ts >= cutoff
            ]

            return RULPrediction(
                device_id=UUID(int=0),
                timestamp=datetime.utcnow(),
                rul_days=round(rul_days, 1),
                confidence_lower=round(confidence_lower, 1),
                confidence_upper=round(confidence_upper, 1),
                status=PredictionStatus.AVAILABLE,
                model_name=self._model_metadata.get("model_name", "unknown"),
                model_version=self._model_metadata.get("model_version", "unknown"),
                dataset_version=self._model_metadata.get("dataset_version", "unknown"),
                input_features=features,
                explanation=self._format_explanation(explanation),
                feature_importance=importance,
                previous_rul_days=previous_rul,
                rul_change_days=rul_days - previous_rul if previous_rul else None,
                is_stable=is_stable,
                confidence_level="high"
                if confidence >= 0.8
                else ("medium" if confidence >= 0.6 else "low"),
                counterfactual=None,  # Would be populated in full implementation
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
            confidence_level="low",
            is_stable=False,
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
            features["fsi_score"] = filter_stress.score
            features["fsi_state"] = {"low": 0, "moderate": 1, "high": 2}.get(
                filter_stress.state.value, 0
            )
            features["dp_score"] = filter_stress.differential_pressure_score or 0
            features["flow_dev_score"] = filter_stress.flow_deviation_score or 0
            features["turbidity_score"] = filter_stress.turbidity_exposure_score or 0
            features["cum_vol_score"] = filter_stress.cumulative_volume_score or 0
            features["age_score"] = filter_stress.filter_age_score or 0
            features["op_hours_score"] = filter_stress.operating_hours_score or 0
            features["tds_trend_score"] = filter_stress.tds_trend_score or 0

        if device_features:
            features.update(device_features)

        if hydraulic_intelligence:
            features["dp"] = hydraulic_intelligence.differential_pressure or 0
            features["flow_dev"] = hydraulic_intelligence.flow_deviation_pct or 0
            features["pressure_trend"] = hydraulic_intelligence.pressure_trend or 0
            features["flow_trend"] = hydraulic_intelligence.flow_trend or 0

        if purification_performance:
            features["rejection_rate"] = purification_performance.rejection_rate or 0
            features["recovery"] = purification_performance.recovery_ratio or 0

        return features

    def _get_confidence(self, features: Dict) -> float:
        """Estimate prediction confidence based on feature quality."""
        # In production, use model uncertainty quantification
        # Simplified heuristic
        confidence = 0.85

        # Reduce confidence for missing features
        required_features = ["fsi_score", "dp", "flow_dev", "rejection_rate"]
        missing = sum(1 for f in required_features if f not in features or features[f] == 0)
        confidence -= missing * 0.1

        return max(0.0, min(1.0, confidence))

    def _get_feature_importance(self) -> Dict[str, float]:
        if hasattr(self._model, "feature_importances_"):
            names = self._model_metadata.get("feature_names", [])
            importances = self._model.feature_importances_
            if hasattr(importances, "tolist"):
                importances = importances.tolist()
            return dict(zip(names, importances))
        return {}

    def _generate_explanation(
        self,
        features: Dict,
        rul_days: float,
        confidence: float,
    ) -> Dict:
        factors = []

        if features.get("fsi_score", 0) > 70:
            factors.append("High Filter Stress Index indicates accelerated degradation")
        if features.get("dp", 0) > 150:
            factors.append("High differential pressure indicates fouling")
        if features.get("tds_trend", 0) > 0.5:
            factors.append("Rising TDS trend indicates membrane degradation")
        if features.get("rejection_rate", 100) < 95:
            factors.append("Declining rejection rate suggests membrane degradation")

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
            confidence_level="low",
            is_stable=False,
        )

    def _check_stability(self, rul_days: float) -> Tuple[bool, str]:
        """Check if RUL prediction is stable."""
        if len(self._prediction_history) < 2:
            return True, "Insufficient history for stability check"

        recent_ruls = [
            rul for _, rul in self._prediction_history[-self.config.rul_stability_window_hours :]
        ]
        if len(recent_ruls) < 2:
            return True, "Insufficient history for stability check"

        max_change = max(
            abs(recent_ruls[i] - recent_ruls[i - 1]) / max(recent_ruls[i - 1], 1) * 100
            for i in range(1, len(recent_ruls))
        )

        if max_change > self.config.rul_max_change_per_window_pct:
            return (
                False,
                f"RUL changed by {max_change:.1f}% in window (threshold: {self.config.rul_max_change_per_window_pct}%)",
            )

        return True, "Stable"

    def _generate_counterfactual(self, previous_rul: float) -> CounterfactualAnalysis:
        """Generate what-changed analysis."""
        return CounterfactualAnalysis(
            device_id=UUID(int=0),
            timestamp=datetime.utcnow(),
            previous_rul_days=previous_rul,
            current_rul_days=0,  # Will be set by caller
            rul_change_days=0,
            rul_change_pct=0,
            contributing_changes=[],
            narrative="",
        )

    def get_stability_report(self, device_id: UUID) -> RULStabilityReport:
        """Get RUL stability report for a device."""
        if len(self._prediction_history) < 2:
            return RULStabilityReport(
                device_id=device_id,
                timestamp=datetime.utcnow(),
                window_hours=self.config.rul_stability_window_hours,
                readings_count=len(self._prediction_history),
                rul_values=[],
                max_change_pct=0.0,
                is_stable=True,
                instability_reason="Insufficient data",
            )

        rul_values = [rul for _, rul in self._prediction_history]
        max_change = 0.0
        for i in range(1, len(rul_values)):
            if rul_values[i - 1] > 0:
                change_pct = abs(rul_values[i] - rul_values[i - 1]) / rul_values[i - 1] * 100
                max_change = max(max_change, change_pct)

        is_stable = max_change <= self.config.rul_max_change_per_window_pct
        instability_reason = None if is_stable else f"RUL changed by {max_change:.1f}% in window"

        return RULStabilityReport(
            device_id=device_id,
            timestamp=datetime.utcnow(),
            window_hours=self.config.rul_stability_window_hours,
            readings_count=len(self._prediction_history),
            rul_values=rul_values,
            max_change_pct=max_change,
            is_stable=is_stable,
            instability_reason=instability_reason,
        )

    def register_model(self, model_artifact) -> bool:
        """Register a model in the model registry."""
        # In production, this would persist to database
        # For now, just load the model
        return self.load_model(model_artifact.artifact_path)

    def promote_model(self, model_id: str) -> bool:
        """Promote a model from VALIDATION to ACTIVE."""
        # In production, update database
        return True

    def retire_model(self, model_id: str) -> bool:
        """Retire a model."""
        # In production, update database
        return True

    def register_dataset(self, dataset: DatasetMetadata) -> bool:
        """Register a dataset for training."""
        # In production, persist to database
        return True

    def record_experiment(self, experiment: ExperimentRecord) -> bool:
        """Record an experiment for training data."""
        # In production, persist to database
        return True
