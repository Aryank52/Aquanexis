"""
Unit tests for RUL Machine Learning Pipeline, Controlled Dataset, and Fallback.
"""

import math
from datetime import datetime, timezone
from uuid import uuid4

import pytest

from app.domain.filter_intelligence import (
    FilterHealthIndex,
    FilterHealthState,
    FilterStressIndex,
    FilterStressState,
    HydraulicIntelligence,
    PredictionStatus,
    PurificationPerformance,
    RULPrediction,
)
from app.ml.dataset import generate_controlled_degradation_dataset
from app.ml.model import RULMultivariateModel
from app.services.rul_service import RULService


class TestRULDatasetGeneration:
    """Tests for the controlled degradation dataset generator."""

    def test_dataset_generation_structure(self):
        """Test dataset shape, features, and metadata."""
        X_train, y_train, X_test, y_test, metadata = generate_controlled_degradation_dataset(
            num_samples=100, seed=42
        )
        assert metadata.dataset_id == "controlled-membrane-deg-v1.0"
        assert metadata.provenance == "CONTROLLED_EXPERIMENT"
        assert len(metadata.features) == 15
        assert metadata.target == "rul_days"
        assert len(X_train) == 80
        assert len(y_train) == 80
        assert len(X_test) == 20
        assert len(y_test) == 20

    def test_dataset_features_present(self):
        """Verify essential physical degradation features exist in each row."""
        X_train, y_train, _, _, metadata = generate_controlled_degradation_dataset(
            num_samples=20, seed=42
        )
        required = ["fsi_score", "dp", "flow_dev", "rejection_rate", "age_score"]
        for feat in required:
            assert feat in X_train[0]


class TestRULMultivariateModel:
    """Tests for the candidate regularized multivariate model."""

    def test_model_training_and_prediction(self):
        """Train model and verify predictions and feature importances."""
        X_train, y_train, X_test, y_test, metadata = generate_controlled_degradation_dataset(
            num_samples=80, seed=42
        )

        model = RULMultivariateModel()
        metrics = model.fit(X_train, y_train, epochs=100)
        assert "train_mae" in metrics
        assert model.is_fitted is True

        # Single dict prediction
        pred_single = model.predict(X_test[0])[0]
        assert isinstance(pred_single, float)
        assert pred_single >= 0.0

        # Feature importances
        assert len(model.feature_importances_) == 15
        total_importance = sum(model.feature_importances_)
        assert math.isclose(total_importance, 1.0, abs_tol=1e-3)


class TestRULServicePipeline:
    """Tests for RUL Service handling both ML model and Deterministic Fallback."""

    def test_service_prediction_with_model(self):
        """Service produces validated prediction with confidence interval when model is loaded."""
        service = RULService()
        if service._model is None:
            service.load_model()

        fsi = FilterStressIndex(
            device_id=uuid4(),
            timestamp=datetime.now(timezone.utc),
            score=35.0,
            state=FilterStressState.LOW,
            turbidity_exposure_score=10.0,
            cumulative_volume_score=30.0,
            filter_age_score=25.0,
            operating_hours_score=25.0,
            tds_trend_score=5.0,
        )

        fhi = FilterHealthIndex(
            device_id=uuid4(),
            timestamp=datetime.now(timezone.utc),
            health_score=80,
            state=FilterHealthState.GOOD,
            confidence=0.88,
        )

        hydraulic = HydraulicIntelligence(
            device_id=uuid4(),
            timestamp=datetime.now(timezone.utc),
            differential_pressure=45.0,
            flow_deviation_pct=-10.0,
            pressure_trend=0.1,
            flow_trend=-0.05,
        )

        purification = PurificationPerformance(
            device_id=uuid4(),
            timestamp=datetime.now(timezone.utc),
            rejection_rate=95.0,
            recovery_ratio=80.0,
        )

        prediction = service.predict_rul(
            filter_stress=fsi,
            filter_health=fhi,
            hydraulic_intelligence=hydraulic,
            purification_performance=purification,
        )

        assert isinstance(prediction, RULPrediction)
        assert prediction.rul_days is not None
        assert prediction.rul_days >= 0
        assert prediction.confidence_lower is not None
        assert prediction.confidence_upper is not None
        assert prediction.confidence_upper >= prediction.confidence_lower

    def test_fallback_prediction_when_model_missing(self):
        """When model is absent, service cleanly falls back to deterministic rule."""
        service = RULService()
        service._model = None  # Simulate absent model

        prediction = service._fallback_prediction(
            reason="model_missing",
            status=PredictionStatus.MODEL_MISSING,
        )

        assert prediction.status == PredictionStatus.MODEL_MISSING
        assert prediction.model_name == "fallback"
        assert prediction.model_version == "1.0"
        assert prediction.explanation["fallback"] is True
