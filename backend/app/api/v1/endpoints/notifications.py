"""
Notification API endpoints.
"""

from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_, desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database import get_db
from app.infrastructure.logging import get_logger
from app.infrastructure.security import get_device_claims, verify_api_key
from app.models.notification import (
    NotificationChannel,
    NotificationErrorCategory,
    NotificationOutbox,
    NotificationProviderConfig,
    NotificationStatus,
    NotificationTemplate,
)
from app.schemas.notification import (
    NotificationOutboxResponse,
    NotificationProviderConfigCreate,
    NotificationProviderConfigResponse,
    NotificationProviderConfigUpdate,
    NotificationStatsResponse,
    NotificationTemplateCreate,
    NotificationTemplateResponse,
    NotificationTestRequest,
    NotificationTestResponse,
)
from app.services.notification_service import NotificationService, get_notification_service
from app.services.notification_worker import get_notification_worker

logger = get_logger(__name__)

router = APIRouter(prefix="/notifications", tags=["notifications"])


# ===== Notification Outbox =====


@router.get("", response_model=List[NotificationOutboxResponse])
async def list_notifications(
    device_id: Optional[UUID] = Query(None),
    alert_id: Optional[UUID] = Query(None),
    channel: Optional[NotificationChannel] = Query(None),
    status: Optional[NotificationStatus] = Query(None),
    start: Optional[datetime] = Query(None),
    end: Optional[datetime] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    device_claims=Depends(get_device_claims),
):
    """List notifications with filtering and pagination."""
    query = select(NotificationOutbox)

    if device_id:
        query = query.where(NotificationOutbox.device_id == device_id)
    elif device_claims:
        query = query.where(NotificationOutbox.device_id == device_claims.device_id)

    if alert_id:
        query = query.where(NotificationOutbox.alert_id == alert_id)
    if channel:
        query = query.where(NotificationOutbox.channel == channel)
    if status:
        query = query.where(NotificationOutbox.status == status)
    if start:
        query = query.where(NotificationOutbox.created_at >= start)
    if end:
        query = query.where(NotificationOutbox.created_at <= end)

    query = query.order_by(desc(NotificationOutbox.created_at)).limit(limit).offset(offset)

    result = await db.execute(query)
    notifications = result.scalars().all()

    return [NotificationOutboxResponse.model_validate(n) for n in notifications]


@router.get("/stats", response_model=NotificationStatsResponse)
async def get_notification_stats(
    device_id: Optional[UUID] = Query(None),
    db: AsyncSession = Depends(get_db),
    device_claims=Depends(get_device_claims),
    service: NotificationService = Depends(get_notification_service),
):
    """Get notification delivery statistics."""
    if device_id and device_claims and device_claims.device_id != device_id:
        raise HTTPException(status_code=403, detail="Not authorized for this device")

    target_device = device_id or (device_claims.device_id if device_claims else None)
    stats = await service.get_stats(target_device)

    return NotificationStatsResponse(
        total_pending=stats.total_pending,
        total_processing=stats.total_processing,
        total_sent=stats.total_sent,
        total_retry=stats.total_retry,
        total_dead_letter=stats.total_dead_letter,
        total_failed=stats.total_failed,
    )


@router.get("/{notification_id}", response_model=NotificationOutboxResponse)
async def get_notification(
    notification_id: UUID,
    db: AsyncSession = Depends(get_db),
    device_claims=Depends(get_device_claims),
):
    """Get a single notification by ID."""
    notification = await db.get(NotificationOutbox, notification_id)
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")

    if device_claims and notification.device_id != device_claims.device_id:
        raise HTTPException(status_code=403, detail="Not authorized")

    return NotificationOutboxResponse.model_validate(notification)


@router.post("/{notification_id}/retry", response_model=NotificationOutboxResponse)
async def retry_notification(
    notification_id: UUID,
    db: AsyncSession = Depends(get_db),
    device_claims=Depends(get_device_claims),
    service: NotificationService = Depends(get_notification_service),
):
    """Retry a failed/dead-letter notification."""
    notification = await db.get(NotificationOutbox, notification_id)
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")

    if device_claims and notification.device_id != device_claims.device_id:
        raise HTTPException(status_code=403, detail="Not authorized")

    success = await service.retry_dead_letter(notification_id)
    if not success:
        raise HTTPException(
            status_code=400,
            detail="Cannot retry notification (not in dead-letter state or not found)",
        )

    await db.refresh(notification)
    return NotificationOutboxResponse.model_validate(notification)


@router.post("/{notification_id}/cancel", response_model=NotificationOutboxResponse)
async def cancel_notification(
    notification_id: UUID,
    db: AsyncSession = Depends(get_db),
    device_claims=Depends(get_device_claims),
    service: NotificationService = Depends(get_notification_service),
):
    """Cancel a pending notification."""
    notification = await db.get(NotificationOutbox, notification_id)
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")

    if device_claims and notification.device_id != device_claims.device_id:
        raise HTTPException(status_code=403, detail="Not authorized")

    success = await service.cancel_notification(notification_id)
    if not success:
        raise HTTPException(
            status_code=400, detail="Cannot cancel notification (already sent or in terminal state)"
        )

    await db.refresh(notification)
    return NotificationOutboxResponse.model_validate(notification)


# ===== Provider Configuration =====


@router.get("/providers", response_model=List[NotificationProviderConfigResponse])
async def list_provider_configs(
    device_id: Optional[UUID] = Query(None),
    db: AsyncSession = Depends(get_db),
    device_claims=Depends(get_device_claims),
):
    """List notification provider configurations for a device."""
    if not device_id and device_claims:
        device_id = device_claims.device_id

    if not device_id:
        raise HTTPException(status_code=400, detail="Device ID required")

    if device_claims and device_claims.device_id != device_id:
        raise HTTPException(status_code=403, detail="Not authorized")

    query = select(NotificationProviderConfig).where(
        NotificationProviderConfig.device_id == device_id
    )

    result = await db.execute(query)
    configs = result.scalars().all()

    return [NotificationProviderConfigResponse.model_validate(c) for c in configs]


@router.post(
    "/providers",
    response_model=NotificationProviderConfigResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_provider_config(
    config_data: NotificationProviderConfigCreate,
    db: AsyncSession = Depends(get_db),
    device_claims=Depends(get_device_claims),
    _: bool = Depends(verify_api_key),  # Admin only
):
    """Create or update a notification provider configuration (admin only)."""
    # Verify device exists
    # In production, you'd check device ownership here

    # Check if config already exists for this device/channel
    existing = await db.execute(
        select(NotificationProviderConfig).where(
            and_(
                NotificationProviderConfig.device_id == config_data.device_id,
                NotificationProviderConfig.channel == config_data.channel,
            )
        )
    )
    existing_config = existing.scalar_one_or_none()

    if existing_config:
        # Update existing
        for field, value in config_data.model_dump(exclude_unset=True).items():
            setattr(existing_config, field, value)
        existing_config.updated_at = datetime.now(timezone.utc)
        config = existing_config
    else:
        # Create new
        config = NotificationProviderConfig(**config_data.model_dump())
        db.add(config)

    await db.commit()
    await db.refresh(config)

    logger.info(
        "notification_provider_config_created",
        device_id=str(config.device_id),
        channel=config.channel.value,
    )

    return NotificationProviderConfigResponse.model_validate(config)


@router.put("/providers/{config_id}", response_model=NotificationProviderConfigResponse)
async def update_provider_config(
    config_id: UUID,
    config_update: NotificationProviderConfigUpdate,
    db: AsyncSession = Depends(get_db),
    device_claims=Depends(get_device_claims),
    _: bool = Depends(verify_api_key),  # Admin only
):
    """Update a notification provider configuration (admin only)."""
    config = await db.get(NotificationProviderConfig, config_id)
    if not config:
        raise HTTPException(status_code=404, detail="Provider config not found")

    for field, value in config_update.model_dump(exclude_unset=True).items():
        setattr(config, field, value)
    config.updated_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(config)

    return NotificationProviderConfigResponse.model_validate(config)


@router.delete("/providers/{config_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_provider_config(
    config_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: bool = Depends(verify_api_key),  # Admin only
):
    """Delete a notification provider configuration (admin only)."""
    config = await db.get(NotificationProviderConfig, config_id)
    if not config:
        raise HTTPException(status_code=404, detail="Provider config not found")

    await db.delete(config)
    await db.commit()


# ===== Templates =====


@router.get("/templates", response_model=List[NotificationTemplateResponse])
async def list_templates(
    channel: Optional[NotificationChannel] = Query(None),
    db: AsyncSession = Depends(get_db),
    _: bool = Depends(verify_api_key),  # Admin only
):
    """List notification templates (admin only)."""
    query = select(NotificationTemplate)
    if channel:
        query = query.where(NotificationTemplate.channel == channel)

    query = query.order_by(NotificationTemplate.name)
    result = await db.execute(query)
    templates = result.scalars().all()

    return [NotificationTemplateResponse.model_validate(t) for t in templates]


@router.post(
    "/templates", response_model=NotificationTemplateResponse, status_code=status.HTTP_201_CREATED
)
async def create_template(
    template_data: NotificationTemplateCreate,
    db: AsyncSession = Depends(get_db),
    _: bool = Depends(verify_api_key),  # Admin only
):
    """Create a notification template (admin only)."""
    template = NotificationTemplate(**template_data.model_dump())
    db.add(template)

    try:
        await db.commit()
        await db.refresh(template)
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=f"Template creation failed: {e}")

    return NotificationTemplateResponse.model_validate(template)


# ===== Test Endpoint =====


@router.post("/test", response_model=NotificationTestResponse)
async def test_notification(
    request: NotificationTestRequest,
    db: AsyncSession = Depends(get_db),
    _: bool = Depends(verify_api_key),  # Admin only
):
    """Test a notification provider (admin only)."""
    from app.services.notification_providers import get_provider

    try:
        provider = get_provider(request.channel)

        # Create a mock notification for testing
        from app.models.notification import NotificationOutbox

        mock_notification = NotificationOutbox(
            id=uuid4(),
            device_id=request.device_id or uuid4(),
            alert_id=uuid4(),
            channel=request.channel,
            provider=request.provider or "test",
            recipient=request.recipient,
            template_name=request.template_name,
            template_data=request.template_data
            or {
                "alert_code": "test_alert",
                "severity": "warning",
                "title": "Test Alert",
                "message": "This is a test notification",
                "trigger_source": "test",
                "trigger_value": "test_value",
                "threshold_value": "threshold",
                "evidence": {},
                "device_id": str(request.device_id or "test-device"),
                "created_at": datetime.now(timezone.utc).isoformat(),
            },
        )

        result = await provider.send(mock_notification)

        return NotificationTestResponse(
            success=result.success,
            channel=request.channel,
            recipient=request.recipient,
            error_category=result.error_category,
            error_message=result.error_message,
            provider_response=result.provider_response,
        )

    except Exception as e:
        logger.error("notification_test_failed", error=str(e))
        return NotificationTestResponse(
            success=False,
            channel=request.channel,
            recipient=request.recipient,
            error_category=NotificationErrorCategory.UNKNOWN,
            error_message=str(e),
        )


# ===== Worker Stats =====


@router.get("/worker/stats")
async def get_worker_stats(
    _: bool = Depends(verify_api_key),
):
    """Get notification worker statistics."""

    worker = await get_notification_worker()
    return worker.get_stats()
