"""
Purification Performance model - rejection rate, recovery, efficiency.
"""
import uuid
from datetime import datetime

from sqlalchemy import Column, BigInteger, DateTime, Float, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID

from app.infrastructure.database import Base


class PurificationPerformance(Base):
    """Purification performance metrics."""

    __tablename__ = "purification_performance"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    device_id = Column(UUID(as_uuid=True), ForeignKey("devices.id", ondelete="CASCADE"), nullable=False, index=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    
    rejection_rate = Column(Float, nullable=True)  # %
    recovery_ratio = Column(Float, nullable=True)  # %
    permeate_quality = Column(Float, nullable=True)  # TDS/conductivity of permeate
    feed_quality = Column(Float, nullable=True)  # TDS/conductivity of feed
    efficiency = Column(Float, nullable=True)  # overall efficiency
    permeate_flow = Column(Float, nullable=True)  # L/min
    reject_flow = Column(Float, nullable=True)  # L/min

    __table_args__ = (
        Index("ix_pp_device_timestamp", "device_id", "timestamp"),
    )

    def __repr__(self) -> str:
        return f"<PurificationPerformance(device_id={self.device_id}, rejection={self.rejection_rate}%)>"