"""
Water Quality Score model - derived AquaScore and parameter scores.
"""
import uuid
from datetime import datetime

from sqlalchemy import Column, BigInteger, DateTime, Float, ForeignKey, Index, SmallInteger, String
from sqlalchemy.dialects.postgresql import JSONB, UUID

from app.infrastructure.database import Base


class WaterQualityScore(Base):
    """Derived water quality score with AquaScore and parameter scores."""

    __tablename__ = "water_quality_scores"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    device_id = Column(UUID(as_uuid=True), ForeignKey("devices.id", ondelete="CASCADE"), nullable=False, index=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    
    overall_score = Column(SmallInteger, nullable=False)  # 0-100
    
    # Parameter scores
    tds_score = Column(SmallInteger, nullable=True)
    ph_score = Column(SmallInteger, nullable=True)
    turbidity_score = Column(SmallInteger, nullable=True)
    temp_score = Column(SmallInteger, nullable=True)
    conductivity_score = Column(SmallInteger, nullable=True)
    
    # Trends (JSONB for flexible storage)
    trends = Column(JSONB, nullable=False, server_default='{}')
    
    # Anomalies
    anomaly_score = Column(Float, nullable=True)
    anomaly_flags = Column(JSONB, nullable=False, server_default='{}')

    __table_args__ = (
        Index("ix_wqs_device_timestamp", "device_id", "timestamp"),
    )

    def __repr__(self) -> str:
        return f"<WaterQualityScore(device_id={self.device_id}, score={self.overall_score})>"