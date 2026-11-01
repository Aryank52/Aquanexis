"""
Alert database model.
"""
import enum
import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Index, String, Text, JSON
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.infrastructure.database import Base


class AlertSeverity(str, enum.Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class AlertStatus(str, enum.Enum):
    DETECTED = "detected"
    OPEN = "open"
    ACKNOWLEDGED = "acknowledged"
    SNOOZED = "snoozed"
    RESOLVED = "resolved"
    AUTO_CLEARED = "auto_cleared"


class Alert(Base):
    """Alert entity with full lifecycle tracking."""

    __tablename__ = "alerts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    device_id = Column(UUID(as_uuid=True), ForeignKey("devices.id", ondelete="CASCADE"), nullable=False, index=True)
    
    alert_code = Column(String(64), nullable=False, index=True)
    severity = Column(Enum(AlertSeverity), nullable=False, default=AlertSeverity.INFO)
    status = Column(Enum(AlertStatus), nullable=False, default=AlertStatus.DETECTED, index=True)
    
    title = Column(String(256), nullable=False)
    message = Column(Text, nullable=False)
    trigger_source = Column(String(64), nullable=False)
    trigger_value = Column(JSONB, nullable=True)
    threshold_value = Column(JSONB, nullable=True)
    evidence = Column(JSONB, nullable=False, default=dict)
    
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)
    snoozed_until = Column(DateTime(timezone=True), nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    auto_cleared_at = Column(DateTime(timezone=True), nullable=True)
    
    created_by = Column(String(128), nullable=True)
    acknowledged_by = Column(String(128), nullable=True)
    resolved_by = Column(String(128), nullable=True)
    
    # For tracking rule evaluation
    rule_version = Column(String(32), nullable=True)
    last_evaluated_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("ix_alerts_device_status", "device_id", "status"),
        Index("ix_alerts_device_code_status", "device_id", "alert_code", "status"),
        Index("ix_alerts_created_at", "created_at"),
        Index("ix_alerts_severity_status", "severity", "status"),
    )

    def __repr__(self) -> str:
        return f"<Alert(id={self.id}, device_id={self.device_id}, code={self.alert_code}, status={self.status})>"