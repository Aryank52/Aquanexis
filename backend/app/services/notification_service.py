"""
Notification service - manages outbox queue, delivery, retries, and worker.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import Depends
from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.config import get_settings
from app.infrastructure.database import get_db
from app.infrastructure.logging import get_logger
from app.models.alert import Alert as AlertModel
from app.models.alert import AlertSeverity
from app.models.notification import (
    NotificationChannel,
    NotificationErrorCategory,
    NotificationOutbox,
    NotificationProviderConfig,
    NotificationStatus,
)
from app.services.notification_providers import (
    NotificationResult,
    get_provider,
)

logger = get_logger(__name__)


# Retry configuration
RETRY_BASE_DELAY_SECONDS = 60  # 1 minute
RETRY_MAX_DELAY_SECONDS = 3600  # 1 hour
RETRY_JITTER_FACTOR = 0.1  # 10% jitter


@dataclass
class DeliveryStats:
    """Statistics for notification delivery."""

    total_pending: int = 0
    total_processing: int = 0
    total_sent: int = 0
    total_retry: int = 0
    total_dead_letter: int = 0
    total_failed: int = 0


class NotificationService:
    """Service for managing notification delivery."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.settings = get_settings()

    async def create_notification(
        self,
        alert: AlertModel,
        channel: NotificationChannel,
        recipient: str,
        provider: str,
        template_name: Optional[str] = None,
        template_data: Optional[Dict[str, Any]] = None,
        subject: Optional[str] = None,
        dedupe_key: Optional[str] = None,
        max_attempts: int = 5,
    ) -> Optional[NotificationOutbox]:
        """
        Create a notification in the outbox.
        Returns None if duplicate (same dedupe_key exists).
        """
        # Generate dedupe key if not provided
        if not dedupe_key:
            dedupe_key = f"{alert.id}:{channel.value}:{recipient}"

        # Check for existing notification with same dedupe_key
        existing = await self.db.execute(
            select(NotificationOutbox).where(NotificationOutbox.dedupe_key == dedupe_key)
        )
        if existing.scalar_one_or_none():
            logger.debug(
                "notification_duplicate_skipped",
                alert_id=str(alert.id),
                channel=channel.value,
                dedupe_key=dedupe_key,
            )
            return None

        # Build template data
        if template_data is None:
            template_data = {
                "alert_code": alert.alert_code,
                "severity": alert.severity.value,
                "title": alert.title,
                "message": alert.message,
                "trigger_source": alert.trigger_source,
                "trigger_value": alert.trigger_value,
                "threshold_value": alert.threshold_value,
                "evidence": alert.evidence,
                "device_id": str(alert.device_id),
                "created_at": alert.created_at.isoformat() if alert.created_at else "",
            }

        # Determine template name based on alert code
        if not template_name:
            template_name = alert.alert_code

        # Create notification
        notification = NotificationOutbox(
            alert_id=alert.id,
            device_id=alert.device_id,
            channel=channel,
            provider=provider,
            recipient=recipient,
            subject=subject,
            body="",  # Will be rendered at send time
            template_name=template_name,
            template_data=template_data,
            dedupe_key=dedupe_key,
            max_attempts=max_attempts,
            next_attempt_at=datetime.now(timezone.utc),
        )

        self.db.add(notification)
        await self.db.commit()
        await self.db.refresh(notification)

        logger.info(
            "notification_created",
            notification_id=str(notification.id),
            alert_id=str(alert.id),
            device_id=str(alert.device_id),
            channel=channel.value,
            provider=provider,
        )

        return notification

    async def create_notifications_for_alert(
        self,
        alert: AlertModel,
    ) -> List[NotificationOutbox]:
        """
        Create notifications for all enabled providers for an alert.
        Uses provider configs for the alert's device.
        """
        notifications = []

        # Get provider configs for this device
        configs = await self._get_provider_configs(
            alert.device_id, alert.severity, alert.alert_code
        )

        for config in configs:
            if not config.enabled:
                continue

            channel = config.channel
            provider_name = config.provider
            recipient = (
                config.config.get("recipient")
                or config.config.get("email")
                or config.config.get("url")
            )

            if not recipient:
                logger.warning(
                    "provider_config_missing_recipient",
                    device_id=str(alert.device_id),
                    channel=channel.value,
                    provider=provider_name,
                )
                continue

            # Check rate limit
            if await self._check_rate_limit(config, channel):
                logger.warning(
                    "provider_rate_limited",
                    device_id=str(alert.device_id),
                    channel=channel.value,
                )
                continue

            notification = await self.create_notification(
                alert=alert,
                channel=channel,
                recipient=recipient,
                provider=provider_name,
                template_name=alert.alert_code,
                max_attempts=5,
            )
            if notification:
                notifications.append(notification)

        return notifications

    async def _get_provider_configs(
        self,
        device_id: UUID,
        severity: AlertSeverity,
        alert_code: str,
    ) -> List[NotificationProviderConfig]:
        """Get enabled provider configs for a device matching severity and alert code."""
        query = select(NotificationProviderConfig).where(
            and_(
                NotificationProviderConfig.device_id == device_id,
                NotificationProviderConfig.enabled == True,
            )
        )

        result = await self.db.execute(query)
        configs = result.scalars().all()

        # Filter by severity
        severity_order = {"info": 0, "warning": 1, "critical": 2}
        alert_severity_level = severity_order.get(severity.value, 0)

        filtered = []
        for config in configs:
            min_severity_level = severity_order.get(config.min_severity, 0)
            if alert_severity_level < min_severity_level:
                continue

            # Filter by alert codes if specified
            if config.alert_codes and alert_code not in config.alert_codes:
                continue

            filtered.append(config)

        return filtered

    async def _check_rate_limit(
        self,
        config: NotificationProviderConfig,
        channel: NotificationChannel,
    ) -> bool:
        """Check if provider is rate limited. Returns True if limited."""
        if not config.rate_limit_per_hour:
            return False

        # Count notifications sent in last hour
        hour_ago = datetime.now(timezone.utc) - timedelta(hours=1)
        query = select(func.count(NotificationOutbox.id)).where(
            and_(
                NotificationOutbox.device_id == config.device_id,
                NotificationOutbox.channel == channel,
                NotificationOutbox.status == NotificationStatus.SENT,
                NotificationOutbox.sent_at >= hour_ago,
            )
        )

        result = await self.db.execute(query)
        count = result.scalar() or 0

        return count >= config.rate_limit_per_hour

    async def process_pending_notifications(
        self,
        batch_size: int = 50,
    ) -> Dict[str, int]:
        """
        Process pending notifications in the outbox.
        Returns statistics.
        """
        stats = {"processed": 0, "sent": 0, "retry": 0, "dead_letter": 0, "failed": 0}

        # Get pending notifications ready for delivery
        now = datetime.now(timezone.utc)
        query = (
            select(NotificationOutbox)
            .where(
                and_(
                    NotificationOutbox.status.in_(
                        [
                            NotificationStatus.PENDING,
                            NotificationStatus.RETRY,
                        ]
                    ),
                    or_(
                        NotificationOutbox.next_attempt_at.is_(None),
                        NotificationOutbox.next_attempt_at <= now,
                    ),
                )
            )
            .order_by(NotificationOutbox.next_attempt_at)
            .limit(batch_size)
        )

        result = await self.db.execute(query)
        notifications = result.scalars().all()

        for notification in notifications:
            outcome = await self._deliver_notification(notification)
            stats["processed"] += 1
            if outcome.success:
                stats["sent"] += 1
            elif notification.attempt_count >= notification.max_attempts:
                stats["dead_letter"] += 1
            else:
                stats["retry"] += 1

        return stats

    async def _deliver_notification(
        self,
        notification: NotificationOutbox,
    ) -> NotificationResult:
        """Attempt to deliver a single notification."""
        # Update status to processing
        notification.status = NotificationStatus.PROCESSING
        notification.attempt_count += 1
        await self.db.commit()

        try:
            # Get provider
            provider = get_provider(notification.channel)

            # Send notification
            result = await provider.send(notification)

            if result.success:
                notification.status = NotificationStatus.SENT
                notification.sent_at = datetime.now(timezone.utc)
                notification.last_error = None
                notification.error_category = None
            else:
                # Handle failure
                if notification.attempt_count >= notification.max_attempts:
                    notification.status = NotificationStatus.DEAD_LETTER
                else:
                    notification.status = NotificationStatus.RETRY
                    # Calculate next attempt with exponential backoff
                    delay = min(
                        RETRY_BASE_DELAY_SECONDS * (2 ** (notification.attempt_count - 1)),
                        RETRY_MAX_DELAY_SECONDS,
                    )
                    # Add jitter
                    import random

                    jitter = delay * RETRY_JITTER_FACTOR * random.uniform(-1, 1)
                    delay = max(1, delay + jitter)
                    notification.next_attempt_at = datetime.now(timezone.utc) + timedelta(
                        seconds=delay
                    )

                notification.last_error = result.error_message
                notification.error_category = result.error_category

            notification.updated_at = datetime.now(timezone.utc)
            await self.db.commit()
            await self.db.refresh(notification)

            logger.info(
                "notification_delivery_attempt",
                notification_id=str(notification.id),
                alert_id=str(notification.alert_id),
                attempt=notification.attempt_count,
                success=result.success,
                status=notification.status.value,
                error=result.error_message,
            )

            return result

        except Exception as e:
            logger.error(
                "notification_delivery_exception",
                notification_id=str(notification.id),
                error=str(e),
            )
            notification.status = NotificationStatus.RETRY
            notification.last_error = str(e)
            notification.error_category = NotificationErrorCategory.UNKNOWN
            notification.updated_at = datetime.now(timezone.utc)
            await self.db.commit()

            return NotificationResult(
                success=False,
                error_category=NotificationErrorCategory.UNKNOWN,
                error_message=str(e),
            )

    async def get_stats(self, device_id: Optional[UUID] = None) -> DeliveryStats:
        """Get delivery statistics."""
        stats = DeliveryStats()

        base_query = select(NotificationOutbox.status, func.count(NotificationOutbox.id)).group_by(
            NotificationOutbox.status
        )

        if device_id:
            base_query = base_query.where(NotificationOutbox.device_id == device_id)

        result = await self.db.execute(base_query)
        for status, count in result:
            if status == NotificationStatus.PENDING:
                stats.total_pending = count
            elif status == NotificationStatus.PROCESSING:
                stats.total_processing = count
            elif status == NotificationStatus.SENT:
                stats.total_sent = count
            elif status == NotificationStatus.RETRY:
                stats.total_retry = count
            elif status == NotificationStatus.DEAD_LETTER:
                stats.total_dead_letter = count
            elif status in (NotificationStatus.CANCELLED, NotificationStatus.FAILED):
                stats.total_failed += count

        return stats

    async def retry_dead_letter(
        self,
        notification_id: UUID,
    ) -> bool:
        """Retry a dead-letter notification."""
        notification = await self.db.get(NotificationOutbox, notification_id)
        if not notification or notification.status != NotificationStatus.DEAD_LETTER:
            return False

        notification.status = NotificationStatus.PENDING
        notification.attempt_count = 0
        notification.next_attempt_at = datetime.now(timezone.utc)
        notification.last_error = None
        notification.error_category = None
        notification.updated_at = datetime.now(timezone.utc)

        await self.db.commit()
        return True

    async def cancel_notification(
        self,
        notification_id: UUID,
    ) -> bool:
        """Cancel a pending notification."""
        notification = await self.db.get(NotificationOutbox, notification_id)
        if not notification or notification.status in (
            NotificationStatus.SENT,
            NotificationStatus.DEAD_LETTER,
        ):
            return False

        notification.status = NotificationStatus.CANCELLED
        notification.updated_at = datetime.now(timezone.utc)
        await self.db.commit()
        return True


async def get_notification_service(
    db: AsyncSession = Depends(get_db),
) -> NotificationService:
    return NotificationService(db)
