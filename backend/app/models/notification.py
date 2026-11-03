"""
Notification database models.
"""

import enum
import uuid
from datetime import datetime

from sqlalchemy import JSON, Column, DateTime, Enum, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID

from app.infrastructure.database import Base


class NotificationChannel(str, enum.Enum):
    """Notification delivery channels."""

    CONSOLE = "console"
    EMAIL = "email"
    WEBHOOK = "webhook"


class NotificationStatus(str, enum.Enum):
    """Notification delivery status."""

    PENDING = "pending"
    PROCESSING = "processing"
    SENT = "sent"
    RETRY = "retry"
    DEAD_LETTER = "dead_letter"
    CANCELLED = "cancelled"


class NotificationErrorCategory(str, enum.Enum):
    """Error classification for retry logic."""

    TRANSIENT = "transient"  # Network timeout, temporary failure - retry
    PERMANENT = "permanent"  # Invalid config, auth failure - don't retry
    UNKNOWN = "unknown"  # Unknown error - retry with backoff


class NotificationOutbox(Base):
    """Notification outbox/queue for durable delivery."""

    __tablename__ = "notification_outbox"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    alert_id = Column(
        UUID(as_uuid=True), ForeignKey("alerts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    device_id = Column(
        UUID(as_uuid=True), ForeignKey("devices.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Delivery configuration
    channel = Column(Enum(NotificationChannel), nullable=False)
    provider = Column(String(32), nullable=False)  # e.g., "console", "smtp", "webhook"
    recipient = Column(String(256), nullable=False)  # email address, webhook URL, etc.

    # Message content
    subject = Column(String(256), nullable=True)
    body = Column(Text, nullable=False)
    template_name = Column(String(64), nullable=True)
    template_data = Column(JSONB, nullable=True)

    # Deduplication
    dedupe_key = Column(String(128), nullable=False, index=True)

    # Status tracking
    status = Column(
        Enum(NotificationStatus), nullable=False, default=NotificationStatus.PENDING, index=True
    )
    error_category = Column(Enum(NotificationErrorCategory), nullable=True)
    last_error = Column(Text, nullable=True)

    # Retry logic
    attempt_count = Column(Integer, nullable=False, default=0)
    max_attempts = Column(Integer, nullable=False, default=5)
    next_attempt_at = Column(DateTime(timezone=True), nullable=True, index=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    sent_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    __table_args__ = (
        Index("ix_notification_outbox_device_status", "device_id", "status"),
        Index("ix_notification_outbox_alert_channel", "alert_id", "channel"),
        Index("ix_notification_outbox_next_attempt", "next_attempt_at", "status"),
        Index("ix_notification_outbox_dedupe", "dedupe_key", unique=True),
    )


class NotificationProviderConfig(Base):
    """Notification provider configuration per device/user."""

    __tablename__ = "notification_provider_config"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    device_id = Column(
        UUID(as_uuid=True), ForeignKey("devices.id", ondelete="CASCADE"), nullable=False, index=True
    )

    channel = Column(Enum(NotificationChannel), nullable=False)
    provider = Column(String(32), nullable=False)
    enabled = Column(
        JSON, nullable=False, default=True
    )  # Boolean but stored as JSON for flexibility

    # Provider-specific config (encrypted in production)
    config = Column(
        JSONB, nullable=False, default=dict
    )  # e.g., {"email": "user@example.com", "webhook_url": "..."}

    # Severity filters
    min_severity = Column(String(16), nullable=False, default="info")  # info, warning, critical
    alert_codes = Column(JSON, nullable=True)  # Optional list of alert codes to notify for

    # Rate limiting per provider
    rate_limit_per_hour = Column(Integer, nullable=True)

    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    __table_args__ = (
        Index(
            "ix_notification_provider_config_device_channel", "device_id", "channel", unique=True
        ),
    )


class NotificationTemplate(Base):
    """Notification templates per alert code/severity."""

    __tablename__ = "notification_template"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(64), nullable=False, unique=True, index=True)
    channel = Column(Enum(NotificationChannel), nullable=False)

    # Template content (Jinja2 syntax)
    subject_template = Column(String(256), nullable=True)
    body_template = Column(Text, nullable=False)

    # Context variables available: alert_code, severity, title, message, trigger_value, threshold_value, evidence, device_id, created_at
    description = Column(Text, nullable=True)

    is_default = Column(JSON, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )
