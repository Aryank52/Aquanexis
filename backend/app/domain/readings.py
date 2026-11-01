"""
Sensor Reading domain models - pure Python, no framework dependencies.
"""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any, Literal
from uuid import UUID


class QualityState(str, Enum):
    """Quality state for individual sensor readings."""
    VALID = "valid"
    SUSPECT = "suspect"
    MISSING = "missing"
    OUT_OF_RANGE = "out_of_range"
    CALIBRATION_DUE = "calibration_due"


class OverallQuality(str, Enum):
    """Overall reading quality."""
    GOOD = "good"
    SUSPECT = "suspect"
    BAD = "bad"


@dataclass
class QualityFlag:
    """Quality flag for a single sensor."""
    state: QualityState = QualityState.VALID
    message: Optional[str] = None
    expected_range: Optional[tuple] = None
    actual_value: Optional[float] = None


@dataclass
class QualityFlags:
    """Quality flags for all sensors in a reading."""
    tds: QualityFlag = field(default_factory=QualityFlag)
    conductivity: QualityFlag = field(default_factory=QualityFlag)
    ph: QualityFlag = field(default_factory=QualityFlag)
    turbidity: QualityFlag = field(default_factory=QualityFlag)
    temperature: QualityFlag = field(default_factory=QualityFlag)
    flow_rate: QualityFlag = field(default_factory=QualityFlag)
    inlet_pressure: QualityFlag = field(default_factory=QualityFlag)
    outlet_pressure: QualityFlag = field(default_factory=QualityFlag)
    tank_level: QualityFlag = field(default_factory=QualityFlag)
    leak: QualityFlag = field(default_factory=QualityFlag)
    pump_current: QualityFlag = field(default_factory=QualityFlag)
    pump_power: QualityFlag = field(default_factory=QualityFlag)

    def to_dict(self) -> Dict[str, Any]:
        return {
            k: {"state": v.state.value, "message": v.message, "expected_range": v.expected_range, "actual_value": v.actual_value}
            for k, v in self.__dict__.items()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "QualityFlags":
        flags = cls()
        for k, v in data.items():
            if hasattr(flags, k):
                flag = QualityFlag(
                    state=QualityState(v.get("state", "valid")),
                    message=v.get("message"),
                    expected_range=v.get("expected_range"),
                    actual_value=v.get("actual_value")
                )
                setattr(flags, k, flag)
        return flags

    def overall(self) -> OverallQuality:
        """Compute overall quality from individual flags."""
        states = [getattr(self, k).state for k in self.__dict__.keys()]
        if any(s == QualityState.OUT_OF_RANGE for s in states):
            return OverallQuality.BAD
        if any(s in (QualityState.SUSPECT, QualityState.CALIBRATION_DUE) for s in states):
            return OverallQuality.SUSPECT
        if all(s == QualityState.MISSING for s in states):
            return OverallQuality.BAD
        return OverallQuality.GOOD


@dataclass
class SensorReadingInput:
    """Input sensor reading from device."""
    tds: Optional[float] = None              # Total Dissolved Solids (ppm)
    conductivity: Optional[float] = None     # Electrical Conductivity (µS/cm)
    ph: Optional[float] = None               # pH (0-14)
    turbidity: Optional[float] = None        # Turbidity (NTU)
    temperature: Optional[float] = None      # Temperature (°C)
    flow_rate: Optional[float] = None        # Flow rate (L/min)
    inlet_pressure: Optional[float] = None   # Inlet pressure (kPa)
    outlet_pressure: Optional[float] = None  # Outlet pressure (kPa)
    tank_level: Optional[float] = None       # Tank level (%)
    leak: Optional[bool] = None              # Leak detected
    pump_current: Optional[float] = None     # Pump current (A)
    pump_power: Optional[float] = None       # Pump power (W)
    uv_state: Optional[bool] = None          # UV lamp state


@dataclass
class TelemetryPayload:
    """Complete telemetry payload from device."""
    device_id: UUID
    timestamp: datetime
    sequence: Optional[int] = None
    firmware_version: Optional[str] = None
    readings: SensorReadingInput = field(default_factory=SensorReadingInput)
    quality: Optional[QualityFlags] = None  # Device-reported quality (optional)


@dataclass
class SensorReading:
    """Stored sensor reading with quality assessment."""
    id: int
    device_id: UUID
    timestamp: datetime
    ingestion_timestamp: datetime
    sequence: Optional[int] = None
    tds: Optional[float] = None
    conductivity: Optional[float] = None
    ph: Optional[float] = None
    turbidity: Optional[float] = None
    temperature: Optional[float] = None
    flow_rate: Optional[float] = None
    inlet_pressure: Optional[float] = None
    outlet_pressure: Optional[float] = None
    tank_level: Optional[float] = None
    leak: Optional[bool] = None
    pump_current: Optional[float] = None
    pump_power: Optional[float] = None
    uv_state: Optional[bool] = None
    quality_flags: QualityFlags = field(default_factory=QualityFlags)
    overall_quality: OverallQuality = OverallQuality.GOOD


@dataclass
class BatchTelemetryPayload:
    """Batch telemetry payload for buffered readings."""
    device_id: UUID
    firmware_version: Optional[str] = None
    readings: list[TelemetryPayload] = field(default_factory=list)


@dataclass
class BatchTelemetryResult:
    """Result of batch ingestion."""
    accepted: int = 0
    rejected: int = 0
    duplicates: int = 0
    invalid: int = 0
    errors: list[Dict[str, Any]] = field(default_factory=list)