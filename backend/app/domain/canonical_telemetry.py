"""
Canonical Telemetry Contract and Security Protocol for AquaNexis.
Unified contract shared by:
ESP32 Firmware -> Ingestion API -> Persistence DB -> Analytics Pipeline -> Frontend UI -> Simulator
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, List, Literal, Optional, Tuple
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class TelemetryProvenance(str, Enum):
    MEASURED = "MEASURED"  # Physical reading from hardware (ESP32)
    SIMULATED = "SIMULATED"  # Synthetic reading from Python simulator / DEMO_MODE
    CALCULATED = "CALCULATED"  # Derived metric (e.g., AquaScore, recovery ratio)
    MODEL_PREDICTED = "MODEL_PREDICTED"  # ML or deterministic prognostics (e.g. RUL)


class DeviceLifecycleState(str, Enum):
    ACTIVE = "ACTIVE"
    DEGRADED = "DEGRADED"
    MAINTENANCE = "MAINTENANCE"
    OFFLINE = "OFFLINE"
    ERROR = "ERROR"


class TelemetryDataQuality(str, Enum):
    GOOD = "GOOD"
    SUSPECT = "SUSPECT"
    BAD = "BAD"


CANONICAL_SENSOR_UNITS: Dict[str, str] = {
    "tds": "ppm",
    "conductivity": "µS/cm",
    "ec": "µS/cm",
    "ph": "pH",
    "turbidity": "NTU",
    "temperature": "°C",
    "flow_rate": "L/min",
    "inlet_pressure": "kPa",
    "outlet_pressure": "kPa",
    "tank_level": "%",
    "leak": "bool",
    "pump_current": "A",
    "pump_power": "W",
    "permeate_flow": "L/min",
    "reject_flow": "L/min",
    "uv_state": "bool",
    "vibration": "g",
}


@dataclass
class CanonicalTelemetryRecord:
    """Canonical domain representation of a verified telemetry reading."""

    device_id: UUID
    timestamp: datetime
    sequence_number: int
    sensor_values: Dict[str, Optional[float | bool]]
    units: Dict[str, str]
    calibration_state: Dict[str, Any]
    firmware_version: str
    data_quality: TelemetryDataQuality
    provenance: TelemetryProvenance
    device_state: DeviceLifecycleState
    received_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def get_value(self, sensor: str) -> Optional[float | bool]:
        return self.sensor_values.get(sensor)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "device_id": str(self.device_id),
            "timestamp": self.timestamp.isoformat(),
            "received_at": self.received_at.isoformat(),
            "sequence_number": self.sequence_number,
            "sensor_values": self.sensor_values,
            "units": self.units,
            "calibration_state": self.calibration_state,
            "firmware_version": self.firmware_version,
            "data_quality": self.data_quality.value,
            "provenance": self.provenance.value,
            "device_state": self.device_state.value,
        }


class CanonicalTelemetryPayload(BaseModel):
    """Pydantic schema enforcing the canonical telemetry wire contract."""

    device_id: UUID
    timestamp: datetime
    sequence_number: int = Field(
        ..., ge=1, description="Strictly positive monotonic sequence number"
    )
    sensor_values: Dict[str, Optional[float | bool]] = Field(
        default_factory=dict,
        description="Core & secondary sensor values (tds, ec, ph, turbidity, temp, flow, pressure, etc.)",
    )
    units: Dict[str, str] = Field(default_factory=lambda: CANONICAL_SENSOR_UNITS.copy())
    calibration_state: Dict[str, Any] = Field(default_factory=dict)
    firmware_version: str = Field(..., min_length=1, max_length=64)
    data_quality: Literal["GOOD", "SUSPECT", "BAD"] = "GOOD"
    provenance: Literal["MEASURED", "SIMULATED"] = Field(
        ...,
        description="Explicit provenance: MEASURED for physical ESP32, SIMULATED for simulator readings",
    )
    device_state: Literal["ACTIVE", "DEGRADED", "MAINTENANCE", "OFFLINE", "ERROR"] = "ACTIVE"

    @field_validator("timestamp")
    @classmethod
    def validate_timestamp_tz(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            return v.replace(tzinfo=timezone.utc)
        return v

    def to_record(self) -> CanonicalTelemetryRecord:
        return CanonicalTelemetryRecord(
            device_id=self.device_id,
            timestamp=self.timestamp,
            sequence_number=self.sequence_number,
            sensor_values=self.sensor_values,
            units={**CANONICAL_SENSOR_UNITS, **self.units},
            calibration_state=self.calibration_state,
            firmware_version=self.firmware_version,
            data_quality=TelemetryDataQuality(self.data_quality),
            provenance=TelemetryProvenance(self.provenance),
            device_state=DeviceLifecycleState(self.device_state),
        )


class DeviceSecurityManager:
    """
    Handles device security: sequence/replay protection, timestamp validation,
    per-device authorization, and security event auditing.
    """

    def __init__(self, max_clock_skew_seconds: int = 300, max_stale_seconds: int = 86400) -> None:
        self.max_clock_skew = timedelta(seconds=max_clock_skew_seconds)
        self.max_stale = timedelta(seconds=max_stale_seconds)
        # In-memory sequence tracker: device_id -> last_sequence_number
        self._last_sequences: Dict[UUID, int] = {}
        # Audit log for security & state events
        self.audit_log: List[Dict[str, Any]] = []

    def register_device_sequence(self, device_id: UUID, initial_sequence: int = 0) -> None:
        """Initialize or reset sequence tracking for a device."""
        self._last_sequences[device_id] = initial_sequence

    def get_last_sequence(self, device_id: UUID) -> Optional[int]:
        return self._last_sequences.get(device_id)

    def validate_packet(
        self,
        payload: CanonicalTelemetryPayload,
        authenticated_device_id: Optional[UUID] = None,
        is_buffered_batch: bool = False,
    ) -> Tuple[bool, Optional[str], Optional[int]]:
        """
        Validate packet against security rules:
        1. Device authorization: authenticated token device_id must match payload device_id.
        2. Timestamp validation: reject timestamps > max_clock_skew in future or > max_stale in past.
        3. Sequence/replay protection: sequence_number must be strictly > last_seen sequence.
        Returns: (is_valid, error_reason, suggested_status_code)
        """
        now = datetime.now(timezone.utc)

        # 1. Device Authorization Check
        if authenticated_device_id is not None and authenticated_device_id != payload.device_id:
            reason = f"Device identity mismatch: token claims {authenticated_device_id} but payload is {payload.device_id}"
            self._log_audit(payload.device_id, "AUTH_DEVICE_MISMATCH", reason)
            return False, reason, 403

        # 2. Timestamp Validation
        payload_ts = payload.timestamp
        if payload_ts.tzinfo is None:
            payload_ts = payload_ts.replace(tzinfo=timezone.utc)

        if payload_ts > now + self.max_clock_skew:
            reason = f"Clock skew rejected: payload timestamp {payload_ts.isoformat()} is >5 minutes in the future"
            self._log_audit(payload.device_id, "CLOCK_SKEW_FUTURE", reason)
            return False, reason, 422

        if not is_buffered_batch and payload_ts < now - self.max_stale:
            reason = f"Stale packet rejected: payload timestamp {payload_ts.isoformat()} is >24 hours old"
            self._log_audit(payload.device_id, "PACKET_EXPIRED_STALE", reason)
            return False, reason, 422

        # 3. Sequence / Replay Protection
        last_seq = self._last_sequences.get(payload.device_id)
        if last_seq is not None:
            if payload.sequence_number <= last_seq:
                reason = f"Replay/out-of-order packet rejected: sequence {payload.sequence_number} <= last seen {last_seq}"
                self._log_audit(payload.device_id, "REPLAY_DETECTED", reason)
                return False, reason, 409

        # Update last sequence
        self._last_sequences[payload.device_id] = payload.sequence_number
        return True, None, None

    def _log_audit(self, device_id: UUID, event_type: str, details: str) -> None:
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "device_id": str(device_id),
            "event_type": event_type,
            "details": details,
        }
        self.audit_log.append(entry)
        if len(self.audit_log) > 500:
            self.audit_log = self.audit_log[-500:]


# Global singleton instance
device_security_manager = DeviceSecurityManager()
