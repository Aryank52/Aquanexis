"""
Safety database models.
"""

import enum
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import JSON, Column, DateTime, Enum, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID

from app.infrastructure.database import Base


class SafetyActionType(enum.Enum):
    """Types of safety actions that can be executed."""

    CLOSE_INLET_VALVE = "close_inlet_valve"
    STOP_PUMP = "stop_pump"
    OPEN_RELIEF_VALVE = "open_relief_valve"
    BOTH_VALVE_AND_PUMP = "both_valve_and_pump"


class SafetyEventType(enum.Enum):
    """Types of safety events that can trigger actions."""

    LEAK_DETECTED = "leak_detected"
    OVERPRESSURE = "overpressure"
    DRY_RUN = "dry_run"
    OVERCURRENT = "overcurrent"


class SafetyActionStatus(enum.Enum):
    """Status of a safety action execution."""

    PENDING = "pending"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    VALIDATION_FAILED = "validation_failed"
    COOLDOWN_ACTIVE = "cooldown_active"


class SafetyEventType(enum.Enum):
    """Types of safety events that can trigger actions."""

    LEAK_DETECTED = "leak_detected"
    OVERPRESSURE = "overpressure"
    DRY_RUN = "dry_run"
    OVERCURRENT = "overcurrent"


class SafetyEventModel(Base):
    """Safety event record for audit trail."""

    __tablename__ = "safety_events"
    __allow_unmapped__ = True

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    device_id = Column(
        UUID(as_uuid=True), ForeignKey("devices.id", ondelete="CASCADE"), nullable=False, index=True
    )

    event_type = Column(Enum(SafetyEventType, native_enum=False), nullable=False)
    action_type = Column(Enum(SafetyActionType, native_enum=False), nullable=True)
    trigger_value = Column(Float, nullable=True)
    threshold_value = Column(Float, nullable=True)

    action_taken = Column(Enum(SafetyActionType, native_enum=False), nullable=True)
    action_status = Column(Enum(SafetyActionStatus, native_enum=False), nullable=True)

    trigger_value = Column(Float, nullable=True)
    threshold_value = Column(Float, nullable=True)
    evidence = Column(JSON, nullable=False, default=dict)
    firmware_response = Column(JSON, nullable=True)

    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    executed_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    initiated_by: str = "system"  # "system", "user", "scheduled"
    user_id: Optional[str] = None

    __table_args__ = (
        Index("ix_safety_events_device_created", "device_id", "created_at"),
        Index("ix_safety_events_device_type", "device_id", "event_type"),
    )


class SafetyActionModel(Base):
    """Safety action command log."""

    __tablename__ = "safety_actions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    device_id = Column(
        UUID(as_uuid=True), ForeignKey("devices.id", ondelete="CASCADE"), nullable=False, index=True
    )

    command_id = Column(UUID(as_uuid=True), nullable=False)
    action_type = Column(Enum(SafetyActionType, native_enum=False), nullable=False)
    event_type = Column(Enum(SafetyEventType, native_enum=False), nullable=False)
    trigger_value = Column(Float, nullable=False)
    threshold_value = Column(Float, nullable=False)
    timestamp = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    timeout_sec = Column(Integer, nullable=False, default=5)
    signature = Column(String(256), nullable=True)

    status = Column(
        Enum(SafetyActionStatus, native_enum=False),
        nullable=False,
        default=SafetyActionStatus.PENDING,
    )
    executed_at = Column(DateTime(timezone=True), nullable=True)
    error_message = Column(Text, nullable=True)
    firmware_response = Column(JSON, nullable=True)

    __table_args__ = (
        Index("ix_safety_actions_device_status", "device_id", "status"),
        Index("ix_safety_actions_device_created", "device_id", "timestamp"),
    )
