"""
Filter Health model - Filter Stress Index, Filter Health Index, RUL predictions.
"""

from sqlalchemy import BigInteger, Column, DateTime, Float, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import JSONB, UUID

from app.infrastructure.database import Base


class FilterHealth(Base):
    """Filter health with FSI, FHI, RUL predictions."""

    __tablename__ = "filter_health"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    device_id = Column(
        UUID(as_uuid=True), ForeignKey("devices.id", ondelete="CASCADE"), nullable=False, index=True
    )
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)

    # Filter Stress Index (0-100)
    fsi = Column(Float, nullable=False)

    # Filter Health Index (0-100)
    fhi = Column(Float, nullable=False)

    # Remaining Useful Life
    rul_days = Column(Float, nullable=True)
    rul_confidence_lower = Column(Float, nullable=True)
    rul_confidence_upper = Column(Float, nullable=True)

    # Model metadata
    model_name = Column(String(64), nullable=False)
    model_version = Column(String(32), nullable=False)
    dataset_version = Column(String(32), nullable=True)

    # Input features and explanation
    input_features = Column(JSONB, nullable=False, server_default="{}")
    explanation = Column(JSONB, nullable=True)

    __table_args__ = (Index("ix_fh_device_timestamp", "device_id", "timestamp"),)

    def __repr__(self) -> str:
        return f"<FilterHealth(device_id={self.device_id}, fsi={self.fsi}, fhi={self.fhi}, rul={self.rul_days})>"
