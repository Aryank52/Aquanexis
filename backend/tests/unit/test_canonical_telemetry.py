"""
Unit tests for Canonical Telemetry Contract and Security Protocol.
"""

from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4
import pytest
from pydantic import ValidationError

from app.domain.canonical_telemetry import (
    CANONICAL_SENSOR_UNITS,
    CanonicalTelemetryPayload,
    DeviceLifecycleState,
    DeviceSecurityManager,
    TelemetryProvenance,
)


class TestCanonicalTelemetryContract:
    """Tests for Canonical Telemetry schema and constraints."""

    def test_canonical_sensor_units_completeness(self):
        """Verify all standard sensors have canonical SI/industry units defined."""
        expected_keys = [
            "tds",
            "conductivity",
            "ph",
            "turbidity",
            "temperature",
            "flow_rate",
            "inlet_pressure",
            "outlet_pressure",
            "tank_level",
            "leak",
        ]
        for key in expected_keys:
            assert key in CANONICAL_SENSOR_UNITS
            assert isinstance(CANONICAL_SENSOR_UNITS[key], str)

    def test_valid_simulated_payload(self):
        """Test valid simulated telemetry payload."""
        device_id = uuid4()
        payload = CanonicalTelemetryPayload(
            device_id=device_id,
            sequence_number=42,
            timestamp=datetime.now(timezone.utc),
            sensor_values={
                "tds": 180.5,
                "ph": 7.2,
                "flow_rate": 2.1,
                "inlet_pressure": 350.0,
            },
            provenance="SIMULATED",
            data_quality="GOOD",
            device_state="ACTIVE",
            firmware_version="v1.0.0",
        )
        assert payload.provenance == "SIMULATED"
        assert payload.device_state == "ACTIVE"
        assert payload.sequence_number == 42
        assert payload.sensor_values["tds"] == 180.5
        assert payload.units["tds"] == "ppm"

    def test_valid_measured_payload(self):
        """Test valid physical hardware telemetry payload."""
        device_id = uuid4()
        payload = CanonicalTelemetryPayload(
            device_id=device_id,
            sequence_number=1,
            timestamp=datetime.now(timezone.utc),
            sensor_values={
                "tds": 210.0,
                "turbidity": 1.2,
                "temperature": 24.5,
            },
            provenance="MEASURED",
            data_quality="GOOD",
            calibration_state={"tds": "calibrated_2026-11-01"},
            firmware_version="esp32-v1.2.0",
        )
        assert payload.provenance == "MEASURED"
        assert payload.calibration_state["tds"] == "calibrated_2026-11-01"

    def test_non_positive_sequence_number_rejected(self):
        """Sequence number must be strictly positive (>=1)."""
        with pytest.raises(ValidationError):
            CanonicalTelemetryPayload(
                device_id=uuid4(),
                sequence_number=0,
                timestamp=datetime.now(timezone.utc),
                sensor_values={"tds": 150.0},
                provenance="SIMULATED",
                firmware_version="v1.0",
            )

    def test_record_conversion(self):
        """Test converting payload schema to domain CanonicalTelemetryRecord."""
        device_id = uuid4()
        payload = CanonicalTelemetryPayload(
            device_id=device_id,
            sequence_number=5,
            timestamp=datetime.now(timezone.utc),
            sensor_values={"tds": 170.0},
            provenance="SIMULATED",
            firmware_version="v1.0",
        )
        record = payload.to_record()
        assert record.device_id == device_id
        assert record.sequence_number == 5
        assert record.provenance == TelemetryProvenance.SIMULATED
        assert record.device_state == DeviceLifecycleState.ACTIVE


class TestDeviceSecurityManager:
    """Tests for Device Security Manager (replay protection, clock skew, auth)."""

    def setup_method(self):
        self.mgr = DeviceSecurityManager(max_clock_skew_seconds=60, max_stale_seconds=3600)
        self.device_id = uuid4()

    def _make_payload(self, seq: int, ts: datetime = None, dev_id: UUID = None):
        return CanonicalTelemetryPayload(
            device_id=dev_id or self.device_id,
            sequence_number=seq,
            timestamp=ts or datetime.now(timezone.utc),
            sensor_values={"tds": 150.0},
            provenance="MEASURED",
            firmware_version="v1.0",
        )

    def test_sequence_progression_allowed(self):
        """Strictly increasing sequences are accepted."""
        p1 = self._make_payload(1)
        valid, err, code = self.mgr.validate_packet(p1)
        assert valid is True
        assert err is None

        p2 = self._make_payload(2)
        valid, err, code = self.mgr.validate_packet(p2)
        assert valid is True

        p10 = self._make_payload(10)
        valid, err, code = self.mgr.validate_packet(p10)
        assert valid is True

    def test_replay_sequence_rejected(self):
        """Old or identical sequence numbers must be rejected to prevent replay attacks."""
        p100 = self._make_payload(100)
        self.mgr.validate_packet(p100)

        # Equal sequence
        p_dup = self._make_payload(100)
        valid, err, code = self.mgr.validate_packet(p_dup)
        assert valid is False
        assert code == 409
        assert "Replay" in err

        # Decreasing sequence
        p_old = self._make_payload(99)
        valid, err, code = self.mgr.validate_packet(p_old)
        assert valid is False
        assert code == 409

    def test_excessive_future_timestamp_rejected(self):
        """Timestamps too far in the future must be rejected."""
        far_future = datetime.now(timezone.utc) + timedelta(minutes=5)
        p = self._make_payload(1, ts=far_future)
        valid, err, code = self.mgr.validate_packet(p)
        assert valid is False
        assert code == 422
        assert "Clock skew" in err

    def test_stale_past_timestamp_rejected(self):
        """Stale unbuffered packets older than max_stale must be rejected."""
        far_past = datetime.now(timezone.utc) - timedelta(hours=2)
        p = self._make_payload(1, ts=far_past)
        valid, err, code = self.mgr.validate_packet(p, is_buffered_batch=False)
        assert valid is False
        assert code == 422
        assert "Stale" in err

    def test_device_auth_matching_id(self):
        """Token with matching device_id claims succeeds."""
        p = self._make_payload(1)
        valid, err, code = self.mgr.validate_packet(p, authenticated_device_id=self.device_id)
        assert valid is True
        assert err is None

    def test_device_auth_mismatched_id(self):
        """Token claiming different device_id is rejected with 403."""
        other_id = uuid4()
        p = self._make_payload(1)
        valid, err, code = self.mgr.validate_packet(p, authenticated_device_id=other_id)
        assert valid is False
        assert code == 403
        assert "Device identity mismatch" in err
