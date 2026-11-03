"""
System Diagnostics model - hydraulic intelligence, pressure, flow, leak, tank, pump.
"""

from sqlalchemy import BigInteger, Column, DateTime, Float, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID

from app.infrastructure.database import Base


class SystemDiagnostics(Base):
    """System diagnostics with hydraulic intelligence."""

    __tablename__ = "system_diagnostics"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    device_id = Column(
        UUID(as_uuid=True), ForeignKey("devices.id", ondelete="CASCADE"), nullable=False, index=True
    )
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)

    # Pressure diagnostics
    pressure_trend = Column(Float, nullable=True)  # kPa/hour
    fouling_indicator = Column(Float, nullable=True)  # 0-1

    # Flow diagnostics
    flow_trend = Column(Float, nullable=True)  # L/min/hour

    # Leak diagnostics
    leak_probability = Column(Float, nullable=True)  # 0-1

    # Tank diagnostics
    tank_fill_rate = Column(Float, nullable=True)  # %/min
    tank_empty_rate = Column(Float, nullable=True)  # %/min

    # Pump diagnostics
    pump_efficiency = Column(Float, nullable=True)  # %
    pump_current_trend = Column(Float, nullable=True)  # A/hour

    __table_args__ = (Index("ix_sd_device_timestamp", "device_id", "timestamp"),)

    def __repr__(self) -> str:
        return f"<SystemDiagnostics(device_id={self.device_id}, timestamp={self.timestamp})>"
