"""
Notification Pydantic schemas for API requests/responses.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field

# Re-export enums from models
from app.models.notification import (
    NotificationChannel,
    NotificationErrorCategory,
    NotificationStatus,
)


class NotificationOutboxResponse(BaseModel):
    """Notification outbox response."""

    id: UUID
    alert_id: UUID
    device_id: UUID
    channel: NotificationChannel
    provider: str
    recipient: str
    subject: Optional[str] = None
    body: str
    template_name: Optional[str] = None
    template_data: Optional[Dict[str, Any]] = None
    dedupe_key: str
    status: NotificationStatus
    error_category: Optional[NotificationErrorCategory] = None
    last_error: Optional[str] = None
    attempt_count: int
    max_attempts: int
    next_attempt_at: Optional[datetime] = None
    created_at: datetime
    sent_at: Optional[datetime] = None
    updated_at: datetime

    class Config:
        from_attributes = True


class NotificationStatsResponse(BaseModel):
    """Notification delivery statistics."""

    total_pending: int = 0
    total_processing: int = 0
    total_sent: int = 0
    total_retry: int = 0
    total_dead_letter: int = 0
    total_failed: int = 0


# Provider Configuration Schemas


class NotificationProviderConfigBase(BaseModel):
    """Base schema for provider config."""

    device_id: UUID
    channel: NotificationChannel
    provider: str
    enabled: bool = True
    config: Dict[str, Any] = Field(default_factory=dict)
    min_severity: str = Field(default="info", pattern="^(info|warning|critical)$")
    alert_codes: Optional[List[str]] = None
    rate_limit_per_hour: Optional[int] = Field(None, ge=1)


class NotificationProviderConfigCreate(NotificationProviderConfigBase):
    """Create provider config request."""

    pass


class NotificationProviderConfigUpdate(BaseModel):
    """Update provider config request."""

    provider: Optional[str] = None
    enabled: Optional[bool] = None
    config: Optional[Dict[str, Any]] = None
    min_severity: Optional[str] = Field(None, pattern="^(info|warning|critical)$")
    alert_codes: Optional[List[str]] = None
    rate_limit_per_hour: Optional[int] = Field(None, ge=1)


class NotificationProviderConfigResponse(NotificationProviderConfigBase):
    """Provider config response."""

    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Template Schemas


class NotificationTemplateCreate(BaseModel):
    """Create template request."""

    name: str = Field(..., min_length=1, max_length=64)
    channel: NotificationChannel
    subject_template: Optional[str] = Field(None, max_length=256)
    body_template: str = Field(..., min_length=1)
    description: Optional[str] = None
    is_default: bool = False


class NotificationTemplateResponse(BaseModel):
    """Template response."""

    id: UUID
    name: str
    channel: NotificationChannel
    subject_template: Optional[str] = None
    body_template: str
    description: Optional[str] = None
    is_default: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Test Schemas


class NotificationTestRequest(BaseModel):
    """Test notification request."""

    device_id: Optional[UUID] = None
    channel: NotificationChannel
    provider: Optional[str] = None
    recipient: str
    template_name: Optional[str] = None
    template_data: Optional[Dict[str, Any]] = None


class NotificationTestResponse(BaseModel):
    """Test notification response."""

    success: bool
    channel: NotificationChannel
    recipient: str
    error_category: Optional[NotificationErrorCategory] = None
    error_message: Optional[str] = None
    provider_response: Optional[Dict[str, Any]] = None
