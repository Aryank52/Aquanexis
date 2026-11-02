"""
Tests for Phase D services.
"""
import pytest
from datetime import datetime, timedelta
from uuid import uuid4

from app.domain.filter_intelligence import (
    FilterStressIndex,
    FilterStressState,
    FilterHealthIndex,
    FilterHealthState,
    FilterStressConfig,
    FilterHealthConfig,
    DEFAULT_FILTER_STRESS_CONFIG,
    DEFAULT_FILTER_HEALTH_CONFIG,
    RULPrediction,
    PredictionStatus,
    PurificationPerformance,
    HydraulicIntelligence,
    FailureRiskLevel,
)

from app.services.filter_stress_service import FilterStressService
from app.services.filter_health_service import FilterHealthService
from app.services.rul_service import RULService
from app.services.failure_risk_service import FailureRiskService
from app.services.water_quality_service import WaterQualityService
from app.services.purification_service import PurificationService
from app.services.hydraulic_service import HydraulicService


class MockReading:
    """Mock sensor reading for testing."""
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


class TestFilterStressService:
    """Tests for FilterStressService."""

    async def test_compute_filter_stress_low(self):
        """Test filter stress with low stress readings."""
        service = FilterStressService()
        reading = MockReading(
            device_id=uuid4(),
            timestamp=datetime.utcnow(),
            pressure=300.0,
            outlet_pressure=280.0,
            flow_rate=1.5,
            turbidity=0.5,
            tds=150.0,
        )
        
        result = await service.compute_filter_stress(
            reading=reading,
            previous_readings=[],
            filter_install_date=datetime.utcnow() - timedelta(days=30),
            cumulative_volume=100.0,
            operating_hours=100.0,
        )
        
        assert isinstance(result, FilterStressIndex)
        assert result.state == FilterStressState.LOW
        assert result.score < 40

    async def test_compute_filter_stress_high(self):
        """Test filter stress with high stress readings."""
        service = FilterStressService()
        reading = MockReading(
            device_id=uuid4(),
            timestamp=datetime.utcnow(),
            pressure=500.0,
            outlet_pressure=200.0,
            flow_rate=0.5,
            turbidity=5.0,
            tds=500.0,
        )
        
        # Create previous readings with high turbidity
        prev_readings = []
        base_time = datetime.utcnow() - timedelta(hours=24)
        for i in range(25):
            prev_readings.append(MockReading(
                device_id=uuid4(),
                timestamp=base_time + timedelta(hours=i),
                turbidity=4.0,
            ))
        
        result = await service.compute_filter_stress(
            reading=reading,
            previous_readings=prev_readings,
            filter_install_date=datetime.utcnow() - timedelta(days=200),
            cumulative_volume=8000.0,
            operating_hours=1500.0,
        )
        
        assert isinstance(result, FilterStressIndex)
        assert result.state == FilterStressState.HIGH
        assert result.score > 70

    def test_differential_pressure_scoring(self):
        """Test differential pressure component scoring."""
        service = FilterStressService()
        
        # Low DP
        reading = MockReading(pressure=200.0, outlet_pressure=180.0)
        score, _ = service._score_differential_pressure(reading, [], DEFAULT_FILTER_STRESS_CONFIG)
        assert score == 0.0
        
        # High DP
        reading = MockReading(pressure=500.0, outlet_pressure=250.0)
        score, _ = service._score_differential_pressure(reading, [], DEFAULT_FILTER_STRESS_CONFIG)
        assert score == 100.0
        
        # Medium DP
        reading = MockReading(pressure=350.0, outlet_pressure=250.0)
        score, _ = service._score_differential_pressure(reading, [], DEFAULT_FILTER_STRESS_CONFIG)
        assert 0 < score < 100


class TestFilterHealthService:
    """Tests for FilterHealthService."""

    def test_compute_filter_health_excellent(self):
        """Test filter health with excellent conditions."""
        service = FilterHealthService()
        
        stress = FilterStressIndex(
            device_id=uuid4(),
            timestamp=datetime.utcnow(),
            state=FilterStressState.LOW,
            score=5.0,
        )
        
        result = service.compute_filter_health(
            filter_stress=stress,
            filter_install_date=datetime.utcnow() - timedelta(days=7),
            cumulative_volume=10.0,
            operating_hours=10.0,
        )
        
        assert isinstance(result, FilterHealthIndex)
        assert result.state == FilterHealthState.EXCELLENT
        assert result.health_score >= 90

    def test_compute_filter_health_critical(self):
        """Test filter health with critical conditions."""
        service = FilterHealthService()
        
        stress = FilterStressIndex(
            device_id=uuid4(),
            timestamp=datetime.utcnow(),
            state=FilterStressState.HIGH,
            score=90.0,
        )
        
        result = service.compute_filter_health(
            filter_stress=stress,
            filter_install_date=datetime.utcnow() - timedelta(days=400),
            cumulative_volume=12000.0,
            operating_hours=3000.0,
        )
        
        assert isinstance(result, FilterHealthIndex)
        assert result.state == FilterHealthState.CRITICAL
        assert result.health_score <= 30


class TestPurificationService:
    """Tests for PurificationService."""

    def test_compute_rejection_rate(self):
        """Test TDS rejection rate calculation."""
        service = PurificationService()
        
        # Normal rejection
        rejection = service.compute_rejection_rate(
            feed_tds=500.0,
            permeate_tds=25.0,
        )
        assert rejection is not None
        assert abs(rejection - 95.0) < 0.1
        
        # Zero feed TDS
        rejection = service.compute_rejection_rate(
            feed_tds=0.0,
            permeate_tds=10.0,
        )
        assert rejection is None
        
        # Missing values
        rejection = service.compute_rejection_rate(
            feed_tds=None,
            permeate_tds=10.0,
        )
        assert rejection is None

    def test_compute_recovery_ratio(self):
        """Test recovery ratio calculation."""
        service = PurificationService()
        
        # From permeate and reject flow
        recovery = service.compute_recovery_from_flows(
            permeate_flow=1.0,
            reject_flow=0.25,
        )
        assert recovery is not None
        assert abs(recovery - 80.0) < 0.1
        
        # From permeate and feed flow
        recovery = service.compute_recovery_from_flows(
            permeate_flow=1.0,
            reject_flow=None,
            feed_flow=1.25,
        )
        assert recovery is not None
        assert abs(recovery - 80.0) < 0.1
        
        # Zero reject flow (100% recovery)
        recovery = service.compute_recovery_from_flows(
            permeate_flow=1.0,
            reject_flow=0.0,
        )
        assert recovery is not None
        assert recovery == 100.0


class TestHydraulicService:
    """Tests for HydraulicService."""

    def test_compute_hydraulic_intelligence(self):
        """Test hydraulic intelligence computation."""
        service = HydraulicService()
        reading = MockReading(
            device_id=uuid4(),
            timestamp=datetime.utcnow(),
            pressure=350.0,
            outlet_pressure=330.0,
            flow_rate=1.2,
            tank_level=50.0,
        )
        
        result = service.compute_hydraulic_intelligence(
            reading=reading,
            previous_readings=[],
            device_baselines={"flow_rate": 1.5},
        )
        
        assert isinstance(result, HydraulicIntelligence)
        assert result.differential_pressure == 20.0
        assert abs(result.flow_deviation_pct - (-20.0)) < 0.001  # (1.2 - 1.5) / 1.5 * 100

    def test_volatility_calculation(self):
        """Test pressure volatility calculation."""
        service = HydraulicService()
        
        values = [350.0, 352.0, 348.0, 351.0, 349.0]
        volatility = service._calculate_volatility(values)
        
        assert volatility >= 0
        assert volatility < 100


class TestRULService:
    """Tests for RULService."""

    def test_fallback_prediction(self):
        """Test fallback prediction when model unavailable."""
        service = RULService()
        
        result = service._fallback_prediction(
            reason="model_missing",
            status=PredictionStatus.MODEL_MISSING,
        )
        
        assert isinstance(result, RULPrediction)
        assert result.status == PredictionStatus.MODEL_MISSING
        assert result.model_name == "fallback"


class TestFailureRiskService:
    """Tests for FailureRiskService."""

    def test_assess_risk_low(self):
        """Test low risk assessment."""
        service = FailureRiskService()
        
        stress = FilterStressIndex(
            device_id=uuid4(),
            timestamp=datetime.utcnow(),
            state=FilterStressState.LOW,
            score=10.0,
        )
        
        health = FilterHealthIndex(
            device_id=uuid4(),
            timestamp=datetime.utcnow(),
            health_score=95,
            state=FilterHealthState.EXCELLENT,
            confidence=0.9,
        )
        
        rul = RULPrediction(
            device_id=uuid4(),
            timestamp=datetime.utcnow(),
            rul_days=200.0,
            status=PredictionStatus.AVAILABLE,
        )
        
        risk = service.assess_risk(
            filter_stress=stress,
            filter_health=health,
            rul_prediction=rul,
            recent_anomalies=[],
            alert_history=[],
        )
        
        assert risk.risk_level == FailureRiskLevel.LOW
        assert risk.risk_score < 40

    def test_assess_risk_high(self):
        """Test high risk assessment."""
        service = FailureRiskService()
        
        stress = FilterStressIndex(
            device_id=uuid4(),
            timestamp=datetime.utcnow(),
            state=FilterStressState.HIGH,
            score=98.0,
        )
        
        health = FilterHealthIndex(
            device_id=uuid4(),
            timestamp=datetime.utcnow(),
            health_score=5,
            state=FilterHealthState.CRITICAL,
            confidence=0.9,
        )
        
        rul = RULPrediction(
            device_id=uuid4(),
            timestamp=datetime.utcnow(),
            rul_days=1.0,
            status=PredictionStatus.AVAILABLE,
        )
        
        risk = service.assess_risk(
            filter_stress=stress,
            filter_health=health,
            rul_prediction=rul,
            recent_anomalies=[],
            alert_history=[],
        )
        
        assert risk.risk_level == FailureRiskLevel.HIGH
        assert risk.risk_score > 70


class TestWaterQualityService:
    """Tests for WaterQualityService."""

    def test_compute_parameter_scores(self):
        """Test parameter scoring."""
        service = WaterQualityService()
        reading = MockReading(
            tds=200.0,
            ph=7.2,
            turbidity=0.5,
            temperature=22.0,
            conductivity=400.0,
        )
        
        scores = service._compute_parameter_scores(reading)
        
        assert len(scores) == 5
        for score in scores:
            assert 0 <= score.score <= 100
            assert score.status in ["ideal", "acceptable", "poor", "missing"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])