"""
Device model - represents a physical water purification device.
"""

import enum
import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, Enum, Index, String
from sqlalchemy.dialects.postgresql import JSONB, UUID

from app.infrastructure.database import Base


class DeviceStatus(str, enum.Enum):
    """Device connection/status states."""

    ACTIVE = "active"
    OFFLINE = "offline"
    DEGRADED = "degraded"
    MAINTENANCE = "maintenance"


class Device(Base):
    """Physical device entity."""

    __tablename__ = "devices"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    serial_number = Column(String(64), unique=True, nullable=False, index=True)
    display_name = Column(String(128), nullable=True)
    model = Column(String(64), nullable=True)
    firmware_version = Column(String(32), nullable=True)

    # Sensor configuration (per-sensor calibration, ranges, etc.)
    sensor_config = Column(JSONB, nullable=False, default=dict)

    # Calibration data (offset, slope per sensor)
    calibration = Column(JSONB, nullable=False, default=dict)

    # Safety configuration (thresholds, actions)
    safety_config = Column(JSONB, nullable=False, default=dict)

    # Capabilities (what sensors/features the device supports)
    capabilities = Column(JSONB, nullable=False, default=dict)

    # Current status
    status = Column(Enum(DeviceStatus), nullable=False, default=DeviceStatus.OFFLINE)
    last_seen = Column(DateTime(timezone=True), nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    # Indexes
    __table_args__ = (Index("ix_devices_status_last_seen", "status", "last_seen"),)

    def __repr__(self) -> str:
        return f"<Device(id={self.id}, serial={self.serial_number}, status={self.status})>"
