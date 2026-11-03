"""
Tests for Alert State Machine Service (Phase G).
"""

import pytest
from datetime import datetime, timezone, timedelta
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.alert_state_machine import AlertStateMachine, TransitionResult, TransitionOutcome
from app.models.alert import Alert as AlertModel, AlertStatus, AlertSeverity
from app.domain.alerts import (
    Alert,
    ALERT_TRANSITIONS,
    AlertSeverity as DomainAlertSeverity,
    AlertStatus as DomainAlertStatus,
)


class MockAlertModel:
    """Mock Alert model for testing."""

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)
        self.id = kwargs.get("id", uuid4())
        self.device_id = kwargs.get("device_id", uuid4())
        self.alert_code = kwargs.get("alert_code", "water_quality_degraded")
        self.severity = kwargs.get("severity", AlertSeverity.WARNING)
        self.status = kwargs.get("status", AlertStatus.DETECTED)
        self.title = kwargs.get("title", "Test Alert")
        self.message = kwargs.get("message", "Test message")
        self.trigger_source = kwargs.get("trigger_source", "test")
        self.trigger_value = kwargs.get("trigger_value", 100)
        self.threshold_value = kwargs.get("threshold_value", 50)
        self.evidence = kwargs.get("evidence", {})
        self.created_at = kwargs.get("created_at", datetime.now(timezone.utc))
        self.acknowledged_at = kwargs.get("acknowledged_at")
        self.snoozed_until = kwargs.get("snoozed_until")
        self.resolved_at = kwargs.get("resolved_at")
        self.auto_cleared_at = kwargs.get("auto_cleared_at")
        self.created_by = kwargs.get("created_by")
        self.acknowledged_by = kwargs.get("acknowledged_by")
        self.resolved_by = kwargs.get("resolved_by")


@pytest.fixture
def mock_db():
    """Mock database session."""
    db = AsyncMock(spec=AsyncSession)
    return db


@pytest.fixture
def state_machine(mock_db):
    """AlertStateMachine instance with mocked DB."""
    return AlertStateMachine(mock_db)


@pytest.fixture
def sample_alert():
    """Create a sample alert in DETECTED state."""
    return MockAlertModel(
        id=uuid4(),
        device_id=uuid4(),
        alert_code="water_quality_degraded",
        severity=AlertSeverity.WARNING,
        status=AlertStatus.DETECTED,
    )


class TestAlertStateMachineTransitions:
    """Tests for alert state transitions."""

    @pytest.mark.asyncio
    async def test_transition_detected_to_open(self, state_machine, sample_alert):
        """Test valid transition from DETECTED to OPEN."""
        alert_id = sample_alert.id

        # Create a fresh mock for each test to avoid state pollution
        fresh_alert = MockAlertModel(
            id=alert_id,
            device_id=sample_alert.device_id,
            alert_code=sample_alert.alert_code,
            severity=sample_alert.severity,
            status=AlertStatus.DETECTED,
        )
        state_machine.db.get = AsyncMock(return_value=fresh_alert)

        outcome = await state_machine.transition(
            alert_id=alert_id,
            new_status=AlertStatus.OPEN,
            user="test_user",
        )

        assert outcome.result == TransitionResult.SUCCESS
        assert outcome.alert is not None
        assert outcome.new_status == AlertStatus.OPEN
        assert "detected" in outcome.message.lower()
        assert "open" in outcome.message.lower()

    @pytest.mark.asyncio
    async def test_transition_open_to_acknowledged(self, state_machine):
        """Test valid transition from OPEN to ACKNOWLEDGED."""
        alert = MockAlertModel(
            id=uuid4(),
            device_id=uuid4(),
            alert_code="pressure_high",
            severity=AlertSeverity.CRITICAL,
            status=AlertStatus.OPEN,
        )
        alert_id = alert.id
        state_machine.db.get = AsyncMock(return_value=alert)

        outcome = await state_machine.transition(
            alert_id=alert_id,
            new_status=AlertStatus.ACKNOWLEDGED,
            user="test_user",
        )

        assert outcome.result == TransitionResult.SUCCESS
        assert outcome.alert.status == AlertStatus.ACKNOWLEDGED
        assert outcome.alert.acknowledged_by == "test_user"
        assert outcome.alert.acknowledged_at is not None

    @pytest.mark.asyncio
    async def test_transition_acknowledged_to_snoozed(self, state_machine):
        """Test valid transition from ACKNOWLEDGED to SNOOZED."""
        alert = MockAlertModel(
            id=uuid4(),
            device_id=uuid4(),
            alert_code="flow_low",
            severity=AlertSeverity.WARNING,
            status=AlertStatus.ACKNOWLEDGED,
            acknowledged_at=datetime.now(timezone.utc),
            acknowledged_by="test_user",
        )
        alert_id = alert.id
        state_machine.db.get = AsyncMock(return_value=alert)

        snoozed_until = datetime.now(timezone.utc) + timedelta(minutes=30)

        outcome = await state_machine.transition(
            alert_id=alert_id,
            new_status=AlertStatus.SNOOZED,
            user="test_user",
            snoozed_until=snoozed_until,
        )

        assert outcome.result == TransitionResult.SUCCESS
        assert outcome.alert.status == AlertStatus.SNOOZED
        assert outcome.alert.snoozed_until == snoozed_until

    @pytest.mark.asyncio
    async def test_transition_snoozed_to_open(self, state_machine):
        """Test valid transition from SNOOZED back to OPEN (snooze expired)."""
        alert = MockAlertModel(
            id=uuid4(),
            device_id=uuid4(),
            alert_code="pressure_low",
            severity=AlertSeverity.WARNING,
            status=AlertStatus.SNOOZED,
            snoozed_until=datetime.now(timezone.utc) - timedelta(minutes=5),  # Expired
        )
        alert_id = alert.id
        state_machine.db.get = AsyncMock(return_value=alert)

        outcome = await state_machine.transition(
            alert_id=alert_id,
            new_status=AlertStatus.OPEN,
            user="system_snooze_expired",
        )

        assert outcome.result == TransitionResult.SUCCESS
        assert outcome.alert.status == AlertStatus.OPEN

    @pytest.mark.asyncio
    async def test_transition_to_resolved(self, state_machine):
        """Test valid transition to RESOLVED from various states."""
        for from_status in [AlertStatus.OPEN, AlertStatus.ACKNOWLEDGED, AlertStatus.SNOOZED]:
            alert = MockAlertModel(
                id=uuid4(),
                device_id=uuid4(),
                alert_code="water_quality_degraded",
                severity=AlertSeverity.WARNING,
                status=from_status,
            )
            alert_id = alert.id
            state_machine.db.get = AsyncMock(return_value=alert)

            outcome = await state_machine.transition(
                alert_id=alert_id,
                new_status=AlertStatus.RESOLVED,
                user="test_user",
            )

            assert outcome.result == TransitionResult.SUCCESS, f"Failed from {from_status}"
            assert outcome.alert.status == AlertStatus.RESOLVED
            assert outcome.alert.resolved_by == "test_user"
            assert outcome.alert.resolved_at is not None

    @pytest.mark.asyncio
    async def test_invalid_transition_detected_to_resolved(self, state_machine, sample_alert):
        """Test invalid transition from DETECTED directly to RESOLVED."""
        alert_id = sample_alert.id
        state_machine.db.get = AsyncMock(return_value=sample_alert)

        outcome = await state_machine.transition(
            alert_id=alert_id,
            new_status=AlertStatus.RESOLVED,
            user="test_user",
        )

        assert outcome.result == TransitionResult.INVALID_TRANSITION
        assert "Invalid transition" in outcome.message

    @pytest.mark.asyncio
    async def test_invalid_transition_from_resolved(self, state_machine):
        """Test transition from terminal RESOLVED state fails."""
        alert = MockAlertModel(
            id=uuid4(),
            device_id=uuid4(),
            alert_code="pressure_high",
            severity=AlertSeverity.CRITICAL,
            status=AlertStatus.RESOLVED,
            resolved_at=datetime.now(timezone.utc),
            resolved_by="test_user",
        )
        alert_id = alert.id
        state_machine.db.get = AsyncMock(return_value=alert)

        outcome = await state_machine.transition(
            alert_id=alert_id,
            new_status=AlertStatus.OPEN,
            user="test_user",
        )

        assert outcome.result == TransitionResult.INVALID_TRANSITION
        assert "terminal state" in outcome.message

    @pytest.mark.asyncio
    async def test_invalid_transition_from_auto_cleared(self, state_machine):
        """Test transition from terminal AUTO_CLEARED state fails."""
        alert = MockAlertModel(
            id=uuid4(),
            device_id=uuid4(),
            alert_code="flow_low",
            severity=AlertSeverity.WARNING,
            status=AlertStatus.AUTO_CLEARED,
            auto_cleared_at=datetime.now(timezone.utc),
        )
        alert_id = alert.id
        state_machine.db.get = AsyncMock(return_value=alert)

        outcome = await state_machine.transition(
            alert_id=alert_id,
            new_status=AlertStatus.OPEN,
            user="test_user",
        )

        assert outcome.result == TransitionResult.INVALID_TRANSITION
        assert "terminal state" in outcome.message

    @pytest.mark.asyncio
    async def test_transition_to_same_state(self, state_machine, sample_alert):
        """Test transition to same state returns ALREADY_IN_STATE."""
        alert_id = sample_alert.id
        state_machine.db.get = AsyncMock(return_value=sample_alert)

        outcome = await state_machine.transition(
            alert_id=alert_id,
            new_status=AlertStatus.DETECTED,
            user="test_user",
        )

        assert outcome.result == TransitionResult.INVALID_TRANSITION
        assert "already in" in outcome.message


class TestAlertStateMachineAutoClear:
    """Tests for auto-clear functionality."""

    @pytest.mark.asyncio
    async def test_auto_clear_supported_code(self, state_machine):
        """Test auto-clear works for supported alert codes."""
        alert = MockAlertModel(
            id=uuid4(),
            device_id=uuid4(),
            alert_code="water_quality_degraded",  # Supports auto-clear
            severity=AlertSeverity.WARNING,
            status=AlertStatus.OPEN,
        )
        state_machine.db.get = AsyncMock(return_value=alert)

        # Mock the transition method
        original_transition = state_machine.transition
        state_machine.transition = AsyncMock(
            return_value=TransitionOutcome(
                result=TransitionResult.SUCCESS,
                alert=alert,
                message="Auto-cleared",
                previous_status=AlertStatus.OPEN,
                new_status=AlertStatus.AUTO_CLEARED,
            )
        )

        outcome = await state_machine.auto_clear_if_applicable(alert, current_condition_met=False)

        assert outcome is not None
        assert outcome.result == TransitionResult.SUCCESS
        assert outcome.new_status == AlertStatus.AUTO_CLEARED

    @pytest.mark.asyncio
    async def test_auto_clear_not_supported_code(self, state_machine):
        """Test auto-clear does NOT work for manual-only codes."""
        alert = MockAlertModel(
            id=uuid4(),
            device_id=uuid4(),
            alert_code="leak_detected",  # Does NOT support auto-clear
            severity=AlertSeverity.CRITICAL,
            status=AlertStatus.OPEN,
        )

        outcome = await state_machine.auto_clear_if_applicable(alert, current_condition_met=False)

        assert outcome is None

    @pytest.mark.asyncio
    async def test_auto_clear_already_terminal(self, state_machine):
        """Test auto-clear does nothing for already terminal alerts."""
        alert = MockAlertModel(
            id=uuid4(),
            device_id=uuid4(),
            alert_code="water_quality_degraded",
            severity=AlertSeverity.WARNING,
            status=AlertStatus.RESOLVED,
            resolved_at=datetime.now(timezone.utc),
        )

        outcome = await state_machine.auto_clear_if_applicable(alert, current_condition_met=False)

        assert outcome is None

    @pytest.mark.asyncio
    async def test_auto_clear_condition_still_met(self, state_machine):
        """Test auto-clear does nothing when condition is still met."""
        alert = MockAlertModel(
            id=uuid4(),
            device_id=uuid4(),
            alert_code="water_quality_degraded",
            severity=AlertSeverity.WARNING,
            status=AlertStatus.OPEN,
        )

        outcome = await state_machine.auto_clear_if_applicable(alert, current_condition_met=True)

        assert outcome is None


class TestAlertStateMachineCanTransition:
    """Tests for can_transition method."""

    def test_can_transition_detected_to_open(self, state_machine):
        """Test DETECTED -> OPEN is valid."""
        alert = MockAlertModel(status=AlertStatus.DETECTED)
        is_valid, reason = state_machine.can_transition(alert, AlertStatus.OPEN)
        assert is_valid is True
        assert reason == ""

    def test_can_transition_detected_to_auto_cleared(self, state_machine):
        """Test DETECTED -> AUTO_CLEARED is valid."""
        alert = MockAlertModel(status=AlertStatus.DETECTED)
        is_valid, reason = state_machine.can_transition(alert, AlertStatus.AUTO_CLEARED)
        assert is_valid is True
        assert reason == ""

    def test_cannot_transition_detected_to_resolved(self, state_machine):
        """Test DETECTED -> RESOLVED is invalid."""
        alert = MockAlertModel(status=AlertStatus.DETECTED)
        is_valid, reason = state_machine.can_transition(alert, AlertStatus.RESOLVED)
        assert is_valid is False
        assert "Invalid transition" in reason

    def test_cannot_transition_from_resolved(self, state_machine):
        """Test any transition from RESOLVED is invalid."""
        alert = MockAlertModel(status=AlertStatus.RESOLVED)
        is_valid, reason = state_machine.can_transition(alert, AlertStatus.OPEN)
        assert is_valid is False
        assert "terminal state" in reason

    def test_cannot_transition_from_auto_cleared(self, state_machine):
        """Test any transition from AUTO_CLEARED is invalid."""
        alert = MockAlertModel(status=AlertStatus.AUTO_CLEARED)
        is_valid, reason = state_machine.can_transition(alert, AlertStatus.OPEN)
        assert is_valid is False
        assert "terminal state" in reason


class TestAlertStateMachineBulkTransition:
    """Tests for bulk transition functionality."""

    @pytest.mark.asyncio
    async def test_bulk_transition_mixed_results(self, state_machine):
        """Test bulk transition with some successes and some failures."""
        alert_ids = [uuid4(), uuid4(), uuid4()]

        # Mock transition to return alternating success/failure
        call_count = [0]

        async def mock_transition(alert_id, new_status, user):
            call_count[0] += 1
            if call_count[0] % 2 == 1:
                return TransitionOutcome(
                    result=TransitionResult.SUCCESS,
                    alert=MockAlertModel(id=alert_id),
                    message="OK",
                    previous_status=AlertStatus.OPEN,
                    new_status=new_status,
                )
            else:
                return TransitionOutcome(
                    result=TransitionResult.INVALID_TRANSITION,
                    alert=MockAlertModel(id=alert_id),
                    message="Invalid",
                    previous_status=AlertStatus.RESOLVED,
                    new_status=new_status,
                )

        state_machine.transition = mock_transition

        result = await state_machine.bulk_transition(
            alert_ids=alert_ids,
            new_status=AlertStatus.RESOLVED,
            user="bulk_user",
        )

        assert result["total"] == 3
        assert len(result["success"]) == 2
        assert len(result["failed"]) == 1


class TestAlertStateMachineCheckAndAutoClear:
    """Tests for check_and_auto_clear_alerts."""

    @pytest.mark.asyncio
    async def test_check_and_auto_clear_multiple_alerts(self, state_machine):
        """Test checking and auto-clearing multiple alerts of same code."""
        device_id = uuid4()
        alert1 = MockAlertModel(
            id=uuid4(),
            device_id=device_id,
            alert_code="water_quality_degraded",
            severity=AlertSeverity.WARNING,
            status=AlertStatus.OPEN,
        )
        alert2 = MockAlertModel(
            id=uuid4(),
            device_id=device_id,
            alert_code="water_quality_degraded",
            severity=AlertSeverity.WARNING,
            status=AlertStatus.ACKNOWLEDGED,
        )

        # Mock db.execute to return both alerts
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [alert1, alert2]
        mock_result = AsyncMock()
        mock_result.scalars = MagicMock(return_value=mock_scalars)
        state_machine.db.execute = AsyncMock(return_value=mock_result)

        # Mock auto_clear_if_applicable
        outcomes = [
            TransitionOutcome(result=TransitionResult.SUCCESS, alert=alert1),
            TransitionOutcome(result=TransitionResult.SUCCESS, alert=alert2),
        ]
        state_machine.auto_clear_if_applicable = AsyncMock(side_effect=outcomes)

        results = await state_machine.check_and_auto_clear_alerts(
            device_id=device_id,
            alert_code="water_quality_degraded",
            condition_met=False,
        )

        assert len(results) == 2
        assert all(r.result == TransitionResult.SUCCESS for r in results)

    @pytest.mark.asyncio
    async def test_check_and_auto_clear_unsupported_code(self, state_machine):
        """Test check_and_auto_clear returns empty for unsupported codes."""
        device_id = uuid4()

        results = await state_machine.check_and_auto_clear_alerts(
            device_id=device_id,
            alert_code="leak_detected",  # Not in AUTO_CLEAR_CODES
            condition_met=False,
        )

        assert results == []


class TestValidTransitionsMap:
    """Tests that the ALERT_TRANSITIONS map is correct."""

    def test_all_statuses_have_transitions_defined(self):
        """Test all alert statuses have transitions defined."""
        for status in DomainAlertStatus:
            assert status in ALERT_TRANSITIONS, f"Missing transitions for {status}"

    def test_detected_transitions(self):
        """Test DETECTED state transitions."""
        assert ALERT_TRANSITIONS[DomainAlertStatus.DETECTED] == [
            DomainAlertStatus.OPEN,
            DomainAlertStatus.AUTO_CLEARED,
        ]

    def test_open_transitions(self):
        """Test OPEN state transitions."""
        assert set(ALERT_TRANSITIONS[DomainAlertStatus.OPEN]) == {
            DomainAlertStatus.ACKNOWLEDGED,
            DomainAlertStatus.SNOOZED,
            DomainAlertStatus.RESOLVED,
            DomainAlertStatus.AUTO_CLEARED,
        }

    def test_acknowledged_transitions(self):
        """Test ACKNOWLEDGED state transitions."""
        assert set(ALERT_TRANSITIONS[DomainAlertStatus.ACKNOWLEDGED]) == {
            DomainAlertStatus.SNOOZED,
            DomainAlertStatus.RESOLVED,
            DomainAlertStatus.AUTO_CLEARED,
        }

    def test_snoozed_transitions(self):
        """Test SNOOZED state transitions."""
        assert set(ALERT_TRANSITIONS[DomainAlertStatus.SNOOZED]) == {
            DomainAlertStatus.OPEN,
            DomainAlertStatus.RESOLVED,
            DomainAlertStatus.AUTO_CLEARED,
        }

    def test_resolved_is_terminal(self):
        """Test RESOLVED is terminal."""
        assert ALERT_TRANSITIONS[DomainAlertStatus.RESOLVED] == []

    def test_auto_cleared_is_terminal(self):
        """Test AUTO_CLEARED is terminal."""
        assert ALERT_TRANSITIONS[DomainAlertStatus.AUTO_CLEARED] == []


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
