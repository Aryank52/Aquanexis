"""
Sensor Reading model - raw immutable telemetry data.
Uses TimescaleDB hypertable for time-series optimization.
"""

from datetime import datetime

from sqlalchemy import BigInteger, Boolean, Column, DateTime, Float, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import JSONB, UUID

from app.infrastructure.database import Base


class SensorReading(Base):
    """
    Raw sensor reading - immutable after insertion.
    Partitioned by time via TimescaleDB hypertable.
    """

    __tablename__ = "sensor_readings"

    # Composite primary key for hypertable partitioning
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    device_id = Column(
        UUID(as_uuid=True), ForeignKey("devices.id", ondelete="CASCADE"), nullable=False, index=True
    )
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    received_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    sequence = Column(
        BigInteger, nullable=True, index=True
    )  # Device sequence number for deduplication

    # Core Level-1 Sensors (Required)
    tds = Column(Float, nullable=True)  # Total Dissolved Solids (ppm)
    ec = Column(Float, nullable=True)  # Electrical Conductivity (µS/cm)
    ph = Column(Float, nullable=True)  # pH (0-14)
    turbidity = Column(Float, nullable=True)  # Turbidity (NTU)
    temperature = Column(Float, nullable=True)  # Temperature (°C)
    flow = Column(Float, nullable=True)  # Flow rate (L/min)
    pressure = Column(Float, nullable=True)  # Inlet pressure (kPa)
    outlet_pressure = Column(Float, nullable=True)  # Outlet pressure (kPa)
    tank_level = Column(Float, nullable=True)  # Tank level (%)
    leak_detected = Column(Boolean, nullable=True)  # Leak sensor state
    pump_current = Column(Float, nullable=True)  # Pump current (A)
    pump_power = Column(Float, nullable=True)  # Pump power (W)

    # Optional Sensors
    permeate_flow = Column(Float, nullable=True)  # Permeate flow (L/min)
    reject_flow = Column(Float, nullable=True)  # Reject flow (L/min)
    uv_state = Column(Boolean, nullable=True)  # UV lamp state
    vibration = Column(Float, nullable=True)  # Vibration (g)

    # Quality Assessment
    quality_flags = Column(JSONB, nullable=False, default=dict)
    overall_quality = Column(String(16), nullable=False, default="GOOD")  # GOOD, SUSPECT, BAD

    # Canonical Telemetry Contract & Provenance
    provenance = Column(
        String(32), nullable=False, default="SIMULATED"
    )  # MEASURED, SIMULATED, CALCULATED, MODEL_PREDICTED
    firmware_version = Column(String(64), nullable=True)
    calibration_state = Column(JSONB, nullable=False, default=dict)
    units = Column(JSONB, nullable=False, default=dict)
    device_state = Column(String(32), nullable=False, default="ACTIVE")

    # Composite primary key (required for TimescaleDB hypertable)
    __table_args__ = (
        Index("ix_sensor_readings_device_timestamp", "device_id", "timestamp"),
        Index("ix_sensor_readings_device_sequence", "device_id", "sequence"),
        # Note: Primary key defined by TimescaleDB hypertable creation
    )

    def __repr__(self) -> str:
        return f"<SensorReading(device_id={self.device_id}, ts={self.timestamp}, quality={self.overall_quality})>"
