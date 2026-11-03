"""
Tests for Auto-resolution of Self-Clearing Alerts (Phase G2).
These tests verify the AlertStateMachine auto-clear logic directly.
"""

import pytest
from datetime import datetime, timezone
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.alert_state_machine import AlertStateMachine, TransitionResult
from app.models.alert import Alert as AlertModel, AlertStatus, AlertSeverity


class MockDevice:
    """Mock device for testing."""

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)
        self.id = kwargs.get("id", uuid4())
        self.safety_config = kwargs.get("safety_config", {})


@pytest.fixture
def mock_db():
    """Mock database session."""
    db = AsyncMock(spec=AsyncSession)
    return db


@pytest.fixture
def sample_device():
    """Create a sample device."""
    return MockDevice(
        id=uuid4(),
        safety_config={
            "pressure_max_kpa": 600.0,
            "flow_min_lpm": 0.1,
            "pump_current_max_a": 2.5,
        },
    )


def make_scalars_all_mock(values):
    """Create a mock for scalars().all()."""
    mock = MagicMock()
    mock.all = MagicMock(return_value=values)
    return mock


class TestAutoClearCodes:
    """Tests for auto-clear code configuration."""

    @pytest.mark.asyncio
    async def test_auto_clear_codes_include_water_quality(self, mock_db):
        """Verify water quality alerts support auto-clear."""
        sm = AlertStateMachine(mock_db)
        assert "water_quality_degraded" in sm.AUTO_CLEAR_CODES
        assert "water_quality_critical" in sm.AUTO_CLEAR_CODES

    @pytest.mark.asyncio
    async def test_auto_clear_codes_include_pressure(self, mock_db):
        """Verify pressure alerts support auto-clear."""
        sm = AlertStateMachine(mock_db)
        assert "pressure_low" in sm.AUTO_CLEAR_CODES
        assert "pressure_high" in sm.AUTO_CLEAR_CODES
        assert "pressure_unstable" in sm.AUTO_CLEAR_CODES
        assert "pressure_differential_high" in sm.AUTO_CLEAR_CODES

    @pytest.mark.asyncio
    async def test_auto_clear_codes_include_flow(self, mock_db):
        """Verify flow alerts support auto-clear."""
        sm = AlertStateMachine(mock_db)
        assert "flow_low" in sm.AUTO_CLEAR_CODES
        assert "flow_high" in sm.AUTO_CLEAR_CODES
        assert "flow_interrupted" in sm.AUTO_CLEAR_CODES
        assert "flow_unstable" in sm.AUTO_CLEAR_CODES

    @pytest.mark.asyncio
    async def test_auto_clear_codes_include_tank(self, mock_db):
        """Verify tank level alerts support auto-clear."""
        sm = AlertStateMachine(mock_db)
        assert "tank_level_low" in sm.AUTO_CLEAR_CODES

    @pytest.mark.asyncio
    async def test_auto_clear_codes_include_pump(self, mock_db):
        """Verify pump alerts support auto-clear."""
        sm = AlertStateMachine(mock_db)
        assert "pump_dry_run_risk" in sm.AUTO_CLEAR_CODES
        assert "pump_excessive_runtime" in sm.AUTO_CLEAR_CODES
        assert "pump_overcurrent" in sm.AUTO_CLEAR_CODES
        assert "pump_abnormal_power" in sm.AUTO_CLEAR_CODES

    @pytest.mark.asyncio
    async def test_auto_clear_codes_include_sensor(self, mock_db):
        """Verify sensor alerts support auto-clear."""
        sm = AlertStateMachine(mock_db)
        assert "sensor_missing" in sm.AUTO_CLEAR_CODES
        assert "sensor_stuck" in sm.AUTO_CLEAR_CODES
        assert "sensor_impossible_value" in sm.AUTO_CLEAR_CODES
        assert "sensor_rapid_change" in sm.AUTO_CLEAR_CODES
        assert "sensor_calibration_due" in sm.AUTO_CLEAR_CODES
        assert "sensor_calibration_overdue" in sm.AUTO_CLEAR_CODES

    @pytest.mark.asyncio
    async def test_auto_clear_codes_include_device(self, mock_db):
        """Verify device alerts support auto-clear."""
        sm = AlertStateMachine(mock_db)
        assert "device_offline" in sm.AUTO_CLEAR_CODES
        assert "device_reconnected" in sm.AUTO_CLEAR_CODES

    @pytest.mark.asyncio
    async def test_auto_clear_codes_include_maintenance(self, mock_db):
        """Verify maintenance alerts support auto-clear."""
        sm = AlertStateMachine(mock_db)
        assert "maintenance_due" in sm.AUTO_CLEAR_CODES


class TestManualOnlyCodes:
    """Test that manual-only codes are NOT auto-cleared."""

    @pytest.mark.asyncio
    async def test_leak_detected_not_auto_clear(self, mock_db):
        """Verify leak_detected requires manual intervention."""
        sm = AlertStateMachine(mock_db)
        assert "leak_detected" not in sm.AUTO_CLEAR_CODES
        assert "leak_detected" in sm.MANUAL_ONLY_CODES

    @pytest.mark.asyncio
    async def test_leak_persistent_not_auto_clear(self, mock_db):
        """Verify leak_persistent requires manual intervention."""
        sm = AlertStateMachine(mock_db)
        assert "leak_persistent" not in sm.AUTO_CLEAR_CODES
        assert "leak_persistent" in sm.MANUAL_ONLY_CODES

    @pytest.mark.asyncio
    async def test_filter_health_critical_not_auto_clear(self, mock_db):
        """Verify filter_health_critical requires manual intervention."""
        sm = AlertStateMachine(mock_db)
        assert "filter_health_critical" not in sm.AUTO_CLEAR_CODES
        assert "filter_health_critical" in sm.MANUAL_ONLY_CODES

    @pytest.mark.asyncio
    async def test_filter_rul_critical_not_auto_clear(self, mock_db):
        """Verify filter_rul_critical requires manual intervention."""
        sm = AlertStateMachine(mock_db)
        assert "filter_rul_critical" not in sm.AUTO_CLEAR_CODES
        assert "filter_rul_critical" in sm.MANUAL_ONLY_CODES

    @pytest.mark.asyncio
    async def test_maintenance_overdue_not_auto_clear(self, mock_db):
        """Verify maintenance_overdue requires manual intervention."""
        sm = AlertStateMachine(mock_db)
        assert "maintenance_overdue" not in sm.AUTO_CLEAR_CODES
        assert "maintenance_overdue" in sm.MANUAL_ONLY_CODES


class TestAutoClearLogic:
    """Tests for the auto-clear logic."""

    @pytest.mark.asyncio
    async def test_auto_clear_if_applicable_returns_none_for_manual_code(self, mock_db):
        """Test auto_clear_if_applicable returns None for manual-only codes."""
        sm = AlertStateMachine(mock_db)

        alert = AlertModel(
            id=uuid4(),
            device_id=uuid4(),
            alert_code="leak_detected",
            severity=AlertSeverity.CRITICAL,
            status=AlertStatus.OPEN,
        )

        result = await sm.auto_clear_if_applicable(alert, current_condition_met=False)
        assert result is None

    @pytest.mark.asyncio
    async def test_auto_clear_if_applicable_returns_none_for_resolved_alert(self, mock_db):
        """Test auto_clear_if_applicable returns None for already resolved alerts."""
        sm = AlertStateMachine(mock_db)

        alert = AlertModel(
            id=uuid4(),
            device_id=uuid4(),
            alert_code="pressure_high",
            severity=AlertSeverity.CRITICAL,
            status=AlertStatus.RESOLVED,
        )

        result = await sm.auto_clear_if_applicable(alert, current_condition_met=False)
        assert result is None

    @pytest.mark.asyncio
    async def test_auto_clear_if_applicable_returns_none_when_condition_met(self, mock_db):
        """Test auto_clear_if_applicable returns None when condition still met."""
        sm = AlertStateMachine(mock_db)

        alert = AlertModel(
            id=uuid4(),
            device_id=uuid4(),
            alert_code="pressure_high",
            severity=AlertSeverity.CRITICAL,
            status=AlertStatus.OPEN,
        )

        result = await sm.auto_clear_if_applicable(alert, current_condition_met=True)
        assert result is None

    @pytest.mark.asyncio
    async def test_auto_clear_if_applicable_calls_transition_when_conditions_met(self, mock_db):
        """Test auto_clear_if_applicable calls transition when all conditions met."""
        sm = AlertStateMachine(mock_db)

        alert = AlertModel(
            id=uuid4(),
            device_id=uuid4(),
            alert_code="pressure_high",
            severity=AlertSeverity.CRITICAL,
            status=AlertStatus.OPEN,
        )

        # Mock the transition method
        original_transition = sm.transition
        mock_transition = AsyncMock(
            return_value=MagicMock(
                result=TransitionResult.SUCCESS,
                alert=alert,
                message="Auto-cleared",
                previous_status=AlertStatus.OPEN,
                new_status=AlertStatus.AUTO_CLEARED,
            )
        )
        sm.transition = mock_transition

        result = await sm.auto_clear_if_applicable(alert, current_condition_met=False)

        assert result is not None
        mock_transition.assert_called_once_with(
            alert_id=alert.id,
            new_status=AlertStatus.AUTO_CLEARED,
            user="system_auto_clear",
        )

    @pytest.mark.asyncio
    async def test_check_and_auto_clear_alerts_returns_empty_for_manual_code(
        self, mock_db, sample_device
    ):
        """Test check_and_auto_clear_alerts returns empty for manual-only codes."""
        sm = AlertStateMachine(mock_db)

        results = await sm.check_and_auto_clear_alerts(
            device_id=sample_device.id,
            alert_code="leak_detected",
            condition_met=False,
        )

        assert results == []

    @pytest.mark.asyncio
    async def test_check_and_auto_clear_alerts_queries_database(self, mock_db, sample_device):
        """Test check_and_auto_clear_alerts queries database for active alerts."""
        sm = AlertStateMachine(mock_db)

        # Mock db.execute to return an alert
        existing_alert = AlertModel(
            id=uuid4(),
            device_id=sample_device.id,
            alert_code="pressure_high",
            severity=AlertSeverity.CRITICAL,
            status=AlertStatus.OPEN,
        )

        mock_result = AsyncMock()
        mock_scalars = MagicMock()
        mock_scalars.all = MagicMock(return_value=[existing_alert])
        mock_result.scalars = MagicMock(return_value=mock_scalars)
        mock_db.execute = AsyncMock(return_value=mock_result)

        # Mock auto_clear_if_applicable
        sm.auto_clear_if_applicable = AsyncMock(
            return_value=MagicMock(
                result=TransitionResult.SUCCESS,
                alert=existing_alert,
            )
        )

        results = await sm.check_and_auto_clear_alerts(
            device_id=sample_device.id,
            alert_code="pressure_high",
            condition_met=False,
        )

        assert len(results) == 1
        mock_db.execute.assert_called_once()
        sm.auto_clear_if_applicable.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
