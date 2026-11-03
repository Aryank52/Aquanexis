"""
Unit tests for Hydraulic Service and Filter Intelligence without fake placeholders.
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID, uuid4
import pytest

from app.services.hydraulic_service import HydraulicService


@dataclass
class MockReading:
    device_id: UUID
    timestamp: datetime
    pressure: Optional[float] = None
    outlet_pressure: Optional[float] = None
    flow_rate: Optional[float] = None
    tank_level: Optional[float] = None


class TestHydraulicIntelligence:
    """Tests for authentic hydraulic analytics with zero fabricated placeholders."""

    def setup_method(self):
        self.service = HydraulicService()
        self.device_id = uuid4()

    def test_missing_outlet_pressure_returns_none(self):
        """When outlet pressure sensor is absent, differential pressure must be None (UNAVAILABLE), not a fake 15% estimate."""
        reading = MockReading(
            device_id=self.device_id,
            timestamp=datetime.now(timezone.utc),
            pressure=400.0,
            outlet_pressure=None,  # No outlet sensor
            flow_rate=2.0,
        )
        intel = self.service.compute_hydraulic_intelligence(
            reading=reading,
            previous_readings=[],
            device_baselines=None,
        )
        assert intel.differential_pressure is None

    def test_present_pressures_computes_legitimate_differential(self):
        """When both inlet and outlet pressure are measured, differential pressure is exact difference."""
        reading = MockReading(
            device_id=self.device_id,
            timestamp=datetime.now(timezone.utc),
            pressure=420.0,
            outlet_pressure=360.0,
            flow_rate=2.0,
        )
        intel = self.service.compute_hydraulic_intelligence(
            reading=reading,
            previous_readings=[],
            device_baselines=None,
        )
        assert intel.differential_pressure == 60.0

    def test_missing_baseline_returns_none_deviation(self):
        """Without a calibrated historical baseline, flow_deviation_pct must be None (UNAVAILABLE), not assuming 1.5 L/min."""
        reading = MockReading(
            device_id=self.device_id,
            timestamp=datetime.now(timezone.utc),
            pressure=350.0,
            outlet_pressure=300.0,
            flow_rate=1.8,
        )
        # No device baselines passed
        intel = self.service.compute_hydraulic_intelligence(
            reading=reading,
            previous_readings=[],
            device_baselines=None,
        )
        assert intel.flow_deviation_pct is None

    def test_established_baseline_computes_exact_deviation(self):
        """When baseline is provided, deviation percentage is calculated against the calibrated baseline."""
        reading = MockReading(
            device_id=self.device_id,
            timestamp=datetime.now(timezone.utc),
            pressure=350.0,
            outlet_pressure=300.0,
            flow_rate=1.5,
        )
        intel = self.service.compute_hydraulic_intelligence(
            reading=reading,
            previous_readings=[],
            device_baselines={"flow_rate": 2.0},
        )
        # Deviation: (1.5 - 2.0) / 2.0 * 100 = -25.0%
        assert intel.flow_deviation_pct == -25.0

    def test_zero_flow_baseline_safety(self):
        """Zero baseline does not cause ZeroDivisionError."""
        reading = MockReading(
            device_id=self.device_id,
            timestamp=datetime.now(timezone.utc),
            pressure=350.0,
            outlet_pressure=300.0,
            flow_rate=1.0,
        )
        intel = self.service.compute_hydraulic_intelligence(
            reading=reading,
            previous_readings=[],
            device_baselines={"flow_rate": 0.0},
        )
        assert intel.flow_deviation_pct is None
