"""
Quality validation service - deterministic validation rules for sensor readings.
Pure Python, no framework dependencies.
"""
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from uuid import UUID

from app.domain.devices import Device, DeviceSensorConfig, DeviceStatus
from app.domain.readings import (
    SensorReadingInput,
    QualityFlags,
    QualityFlag,
    QualityState,
    OverallQuality,
    SensorReading,
)


# Default sensor ranges (configurable per device)
DEFAULT_RANGES = {
    "tds": (0, 2000),              # ppm
    "conductivity": (0, 4000),     # µS/cm
    "ph": (0, 14),                 # pH
    "turbidity": (0, 100),         # NTU
    "temperature": (-10, 60),      # °C
    "flow_rate": (0, 50),          # L/min
    "inlet_pressure": (0, 1000),   # kPa
    "outlet_pressure": (0, 1000),  # kPa
    "tank_level": (0, 100),        # %
    "pump_current": (0, 10),       # A
    "pump_power": (0, 5000),       # W
}

# Maximum rate of change per minute (configurable per device)
DEFAULT_RATE_LIMITS = {
    "tds": 100,                    # ppm/min
    "conductivity": 200,           # µS/cm/min
    "ph": 0.5,                     # pH/min
    "turbidity": 10,               # NTU/min
    "temperature": 5,              # °C/min
    "flow_rate": 5,                # L/min/min
    "inlet_pressure": 100,         # kPa/min
    "outlet_pressure": 100,        # kPa/min
    "tank_level": 20,              # %/min
    "pump_current": 1,             # A/min
    "pump_power": 500,             # W/min
}

# Cross-sensor consistency rules
CROSS_SENSOR_RULES = {
    "tds_conductivity": {
        "fields": ["tds", "conductivity"],
        "ratio_range": (0.5, 0.7),  # TDS ≈ Conductivity * 0.5-0.7
        "message": "TDS/Conductivity ratio outside expected range"
    },
}


@dataclass
class ValidationConfig:
    """Validation configuration."""
    ranges: Dict[str, tuple] = field(default_factory=lambda: DEFAULT_RANGES.copy())
    rate_limits: Dict[str, float] = field(default_factory=lambda: DEFAULT_RATE_LIMITS.copy())
    stale_threshold_seconds: int = 300  # 5 minutes
    duplicate_sequence_window: int = 1000  # track last N sequences


class QualityValidator:
    """Validates sensor readings and assigns quality flags."""

    def __init__(self, config: Optional[ValidationConfig] = None):
        self.config = config or ValidationConfig()
        self._last_readings: Dict[UUID, SensorReading] = {}
        self._sequence_history: Dict[UUID, List[int]] = {}

    def validate(
        self,
        device: Device,
        payload,
        previous_reading: Optional[SensorReading] = None
    ) -> QualityFlags:
        """
        Validate a telemetry payload and return quality flags.
        
        Args:
            device: Device configuration
            payload: Telemetry payload to validate
            previous_reading: Previous reading for rate-of-change checks
            
        Returns:
            QualityFlags with per-sensor quality state
        """
        flags = QualityFlags()
        readings = payload.readings
        
        # Use provided previous reading or lookup from cache
        if previous_reading is None:
            previous_reading = self._last_readings.get(device.id)
        
        # Validate each sensor
        self._validate_range(device, readings, flags)
        self._validate_rate(device, readings, previous_reading, flags, getattr(payload, "timestamp", None))
        self._validate_cross_sensor(readings, flags)
        self._check_stuck_sensor(readings, previous_reading, flags)
        
        return flags

    def _validate_range(
        self,
        device: Device,
        readings: SensorReadingInput,
        flags: QualityFlags
    ) -> None:
        """Validate sensor values against configured ranges."""
        sensor_config = device.sensor_config
        ranges = self.config.ranges
        
        # Map sensor names to config and ranges
        sensors = [
            ("tds", readings.tds, sensor_config.tds, ranges.get("tds")),
            ("conductivity", readings.conductivity, sensor_config.conductivity, ranges.get("conductivity")),
            ("ph", readings.ph, sensor_config.ph, ranges.get("ph")),
            ("turbidity", readings.turbidity, sensor_config.turbidity, ranges.get("turbidity")),
            ("temperature", readings.temperature, sensor_config.temperature, ranges.get("temperature")),
            ("flow_rate", readings.flow_rate, sensor_config.flow_rate, ranges.get("flow_rate")),
            ("inlet_pressure", readings.inlet_pressure, sensor_config.inlet_pressure, ranges.get("inlet_pressure")),
            ("outlet_pressure", readings.outlet_pressure, sensor_config.outlet_pressure, ranges.get("outlet_pressure")),
            ("tank_level", readings.tank_level, sensor_config.tank_level, ranges.get("tank_level")),
            ("pump_current", readings.pump_current, sensor_config.pump_current, ranges.get("pump_current")),
            ("pump_power", readings.pump_power, sensor_config.pump_power, ranges.get("pump_power")),
        ]
        
        for name, value, sensor_cfg, range_limits in sensors:
            flag = getattr(flags, name)
            
            if value is None:
                flag.state = QualityState.MISSING
                flag.message = "Sensor value not provided"
                continue
            
            if not sensor_cfg.enabled:
                flag.state = QualityState.MISSING
                flag.message = "Sensor disabled"
                continue
            
            # Apply calibration
            calibrated_value = value * sensor_cfg.calibration_slope + sensor_cfg.calibration_offset
            flag.actual_value = calibrated_value
            flag.expected_range = range_limits
            
            # Check range
            if range_limits:
                min_val, max_val = range_limits
                if calibrated_value < min_val or calibrated_value > max_val:
                    flag.state = QualityState.OUT_OF_RANGE
                    flag.message = f"Value {calibrated_value} outside range [{min_val}, {max_val}]"
                else:
                    flag.state = QualityState.VALID

    def _validate_rate(
        self,
        device: Device,
        readings: SensorReadingInput,
        previous: Optional[SensorReading],
        flags: QualityFlags,
        current_timestamp: Optional[datetime] = None,
    ) -> None:
        """Validate rate of change against limits."""
        if previous is None:
            return
        
        sensor_config = device.sensor_config
        rate_limits = self.config.rate_limits
        now_ts = current_timestamp or datetime.utcnow()
        prev_ts = getattr(previous, "timestamp", None)
        if prev_ts is None:
            return
        time_diff = (now_ts - prev_ts).total_seconds() / 60.0  # minutes
        
        if time_diff <= 0:
            return
        
        sensors = [
            ("tds", readings.tds, previous.tds, sensor_config.tds, rate_limits.get("tds")),
            ("conductivity", readings.conductivity, previous.conductivity, sensor_config.conductivity, rate_limits.get("conductivity")),
            ("ph", readings.ph, previous.ph, sensor_config.ph, rate_limits.get("ph")),
            ("turbidity", readings.turbidity, previous.turbidity, sensor_config.turbidity, rate_limits.get("turbidity")),
            ("temperature", readings.temperature, previous.temperature, sensor_config.temperature, rate_limits.get("temperature")),
            ("flow_rate", readings.flow_rate, previous.flow_rate, sensor_config.flow_rate, rate_limits.get("flow_rate")),
            ("inlet_pressure", readings.inlet_pressure, previous.inlet_pressure, sensor_config.inlet_pressure, rate_limits.get("inlet_pressure")),
            ("outlet_pressure", readings.outlet_pressure, previous.outlet_pressure, sensor_config.outlet_pressure, rate_limits.get("outlet_pressure")),
            ("tank_level", readings.tank_level, previous.tank_level, sensor_config.tank_level, rate_limits.get("tank_level")),
            ("pump_current", readings.pump_current, previous.pump_current, sensor_config.pump_current, rate_limits.get("pump_current")),
            ("pump_power", readings.pump_power, previous.pump_power, sensor_config.pump_power, rate_limits.get("pump_power")),
        ]
        
        for name, current, prev_val, sensor_cfg, rate_limit in sensors:
            flag = getattr(flags, name)
            
            if current is None or prev_val is None:
                continue
            if not sensor_cfg.enabled:
                continue
            if rate_limit is None:
                continue
            
            # Apply calibration to both
            current_cal = current * sensor_cfg.calibration_slope + sensor_cfg.calibration_offset
            prev_cal = prev_val * sensor_cfg.calibration_slope + sensor_cfg.calibration_offset
            
            rate = abs(current_cal - prev_cal) / time_diff
            if rate > rate_limit:
                flag.state = QualityState.SUSPECT
                flag.message = f"Rate of change {rate:.2f}/min exceeds limit {rate_limit}/min"

    def _validate_cross_sensor(
        self,
        readings: SensorReadingInput,
        flags: QualityFlags
    ) -> None:
        """Validate cross-sensor consistency."""
        # TDS vs Conductivity correlation
        if readings.tds is not None and readings.conductivity is not None:
            ratio = readings.tds / readings.conductivity if readings.conductivity > 0 else 0
            min_ratio, max_ratio = CROSS_SENSOR_RULES["tds_conductivity"]["ratio_range"]
            
            if ratio < min_ratio or ratio > max_ratio:
                flags.tds.state = QualityState.SUSPECT
                flags.conductivity.state = QualityState.SUSPECT
                msg = CROSS_SENSOR_RULES["tds_conductivity"]["message"]
                flags.tds.message = msg
                flags.conductivity.message = msg

    def _check_stuck_sensor(
        self,
        readings: SensorReadingInput,
        previous: Optional[SensorReading],
        flags: QualityFlags
    ) -> None:
        """Check for stuck sensor (same value repeated)."""
        if previous is None:
            return
        
        sensors = [
            ("tds", readings.tds, previous.tds),
            ("conductivity", readings.conductivity, previous.conductivity),
            ("ph", readings.ph, previous.ph),
            ("turbidity", readings.turbidity, previous.turbidity),
            ("temperature", readings.temperature, previous.temperature),
            ("flow_rate", readings.flow_rate, previous.flow_rate),
            ("inlet_pressure", readings.inlet_pressure, previous.inlet_pressure),
            ("outlet_pressure", readings.outlet_pressure, previous.outlet_pressure),
            ("tank_level", readings.tank_level, previous.tank_level),
            ("pump_current", readings.pump_current, previous.pump_current),
            ("pump_power", readings.pump_power, previous.pump_power),
        ]
        
        for name, current, prev_val in sensors:
            flag = getattr(flags, name)
            
            if current is not None and prev_val is not None:
                if current == prev_val:
                    # Could be stuck - mark as suspect but don't override OUT_OF_RANGE
                    if flag.state == QualityState.VALID:
                        flag.state = QualityState.SUSPECT
                        flag.message = "Possible stuck sensor - value unchanged"

    def check_duplicate_sequence(self, device_id: UUID, sequence: Optional[int]) -> bool:
        """Check if sequence number is duplicate."""
        if sequence is None:
            return False
        
        history = self._sequence_history.get(device_id, [])
        if sequence in history:
            return True
        
        # Add to history
        history.append(sequence)
        if len(history) > self.config.duplicate_sequence_window:
            history.pop(0)
        self._sequence_history[device_id] = history
        
        return False

    def update_last_reading(self, reading: SensorReading) -> None:
        """Cache the last reading for rate validation."""
        self._last_readings[reading.device_id] = reading

    def is_stale(self, last_seen: Optional[datetime], now: Optional[datetime] = None) -> bool:
        """Check if device data is stale."""
        if last_seen is None:
            return True
        now = now or datetime.utcnow()
        return (now - last_seen).total_seconds() > self.config.stale_threshold_seconds


# Global validator instance
quality_validator = QualityValidator()