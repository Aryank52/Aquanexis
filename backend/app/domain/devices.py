"""
Device domain models - pure Python, no framework dependencies.
"""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any
from uuid import UUID


class DeviceStatus(str, Enum):
    """Device connection/status states."""
    ACTIVE = "active"
    OFFLINE = "offline"
    DEGRADED = "degraded"
    MAINTENANCE = "maintenance"


@dataclass
class SensorConfig:
    """Per-sensor configuration."""
    enabled: bool = True
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    rate_limit: Optional[float] = None  # max change per minute
    calibration_offset: float = 0.0
    calibration_slope: float = 1.0


@dataclass
class DeviceSensorConfig:
    """Complete sensor configuration for a device."""
    tds: SensorConfig = field(default_factory=SensorConfig)
    conductivity: SensorConfig = field(default_factory=SensorConfig)
    ph: SensorConfig = field(default_factory=SensorConfig)
    turbidity: SensorConfig = field(default_factory=SensorConfig)
    temperature: SensorConfig = field(default_factory=SensorConfig)
    flow_rate: SensorConfig = field(default_factory=SensorConfig)
    inlet_pressure: SensorConfig = field(default_factory=SensorConfig)
    outlet_pressure: SensorConfig = field(default_factory=SensorConfig)
    tank_level: SensorConfig = field(default_factory=SensorConfig)
    leak: SensorConfig = field(default_factory=SensorConfig)
    pump_current: SensorConfig = field(default_factory=SensorConfig)
    pump_power: SensorConfig = field(default_factory=SensorConfig)


@dataclass
class SafetyConfig:
    """Safety thresholds and actions."""
    leak_action: str = "close_inlet_valve"
    leak_validate_with: list[str] = field(default_factory=lambda: ["flow_delta", "pressure_drop"])
    leak_cooldown_sec: int = 300
    pressure_max_kpa: float = 600.0
    pressure_action: str = "open_relief"
    pressure_cooldown_sec: int = 60
    flow_min_lpm: float = 0.1
    dry_run_action: str = "stop_pump"
    dry_run_cooldown_sec: int = 120
    pump_current_max_a: float = 2.5
    overcurrent_action: str = "stop_pump"
    overcurrent_cooldown_sec: int = 180


@dataclass
class Device:
    """Physical device entity."""
    id: UUID
    serial_number: str
    display_name: Optional[str] = None
    model: Optional[str] = None
    firmware_version: Optional[str] = None
    sensor_config: DeviceSensorConfig = field(default_factory=DeviceSensorConfig)
    safety_config: SafetyConfig = field(default_factory=SafetyConfig)
    calibration: Dict[str, Any] = field(default_factory=dict)
    status: DeviceStatus = DeviceStatus.OFFLINE
    last_seen_at: Optional[datetime] = None
    capabilities: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def update_last_seen(self, timestamp: datetime) -> None:
        """Update last seen timestamp and status."""
        self.last_seen_at = timestamp
        self.updated_at = datetime.utcnow()

    def set_status(self, status: DeviceStatus) -> None:
        """Set device status."""
        self.status = status
        self.updated_at = datetime.utcnow()