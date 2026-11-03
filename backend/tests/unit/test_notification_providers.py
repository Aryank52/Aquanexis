"""
Tests for Notification Providers (Phase G3).
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import (
    NotificationOutbox,
    NotificationChannel,
    NotificationStatus,
    NotificationErrorCategory,
)
from app.services.notification_providers import (
    ConsoleNotificationProvider,
    EmailNotificationProvider,
    WebhookNotificationProvider,
    get_provider,
    NotificationResult,
)
from app.services.notification_service import NotificationService
from app.models.alert import Alert as AlertModel, AlertSeverity, AlertStatus


class MockAlert:
    """Mock alert for testing."""

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)
        self.id = kwargs.get("id", uuid4())
        self.device_id = kwargs.get("device_id", uuid4())
        self.alert_code = kwargs.get("alert_code", "test_alert")
        self.severity = kwargs.get("severity", AlertSeverity.WARNING)
        self.status = kwargs.get("status", AlertStatus.OPEN)
        self.title = kwargs.get("title", "Test Alert")
        self.message = kwargs.get("message", "Test message")
        self.trigger_source = kwargs.get("trigger_source", "test")
        self.trigger_value = kwargs.get("trigger_value", {"value": 100})
        self.threshold_value = kwargs.get("threshold_value", {"threshold": 50})
        self.evidence = kwargs.get("evidence", {})
        self.created_at = kwargs.get("created_at", datetime.now(timezone.utc))


class MockNotification:
    """Mock notification outbox for testing."""

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)
        self.id = kwargs.get("id", uuid4())
        self.alert_id = kwargs.get("alert_id", uuid4())
        self.device_id = kwargs.get("device_id", uuid4())
        self.channel = kwargs.get("channel", NotificationChannel.CONSOLE)
        self.provider = kwargs.get("provider", "console")
        self.recipient = kwargs.get("recipient", "test@example.com")
        self.subject = kwargs.get("subject")
        self.body = kwargs.get("body", "")
        self.template_name = kwargs.get("template_name", "default")
        self.template_data = kwargs.get(
            "template_data",
            {
                "alert_code": "test_alert",
                "severity": "warning",
                "title": "Test Alert",
                "message": "Test message",
                "trigger_source": "test",
                "trigger_value": {"value": 100},
                "threshold_value": {"threshold": 50},
                "evidence": {},
                "device_id": "test-device",
                "created_at": datetime.now(timezone.utc).isoformat(),
            },
        )
        self.dedupe_key = kwargs.get("dedupe_key", "test-key")
        self.status = kwargs.get("status", NotificationStatus.PENDING)
        self.error_category = kwargs.get("error_category")
        self.last_error = kwargs.get("last_error")
        self.attempt_count = kwargs.get("attempt_count", 0)
        self.max_attempts = kwargs.get("max_attempts", 5)
        self.next_attempt_at = kwargs.get("next_attempt_at")
        self.created_at = kwargs.get("created_at", datetime.now(timezone.utc))
        self.sent_at = kwargs.get("sent_at")
        self.updated_at = kwargs.get("updated_at", datetime.now(timezone.utc))


@pytest.fixture
def mock_db():
    """Mock database session."""
    db = AsyncMock(spec=AsyncSession)
    return db


@pytest.fixture
def sample_alert():
    """Create a sample alert."""
    return MockAlert(
        id=uuid4(),
        device_id=uuid4(),
        alert_code="water_quality_degraded",
        severity=AlertSeverity.WARNING,
        status=AlertStatus.OPEN,
        title="Water Quality Degraded",
        message="TDS level exceeds threshold",
        trigger_source="tds_sensor",
        trigger_value={"tds_ppm": 600},
        threshold_value={"tds_limit_ppm": 500},
        evidence={"tds_ppm": 600},
    )


class TestConsoleNotificationProvider:
    """Tests for ConsoleNotificationProvider."""

    @pytest.fixture
    def provider(self):
        return ConsoleNotificationProvider({})

    @pytest.mark.asyncio
    async def test_send_console_notification(self, provider):
        """Test sending console notification."""
        notification = MockNotification(
            channel=NotificationChannel.CONSOLE,
            provider="console",
            recipient="console",
            template_name="default",
        )

        result = await provider.send(notification)

        assert result.success is True
        assert result.provider_response is not None
        assert result.provider_response["logged"] is True

    @pytest.mark.asyncio
    async def test_send_with_leak_template(self, provider):
        """Test console notification with leak template."""
        notification = MockNotification(
            channel=NotificationChannel.CONSOLE,
            provider="console",
            recipient="console",
            template_name="leak_detected",
            template_data={
                "alert_code": "leak_detected",
                "severity": "critical",
                "title": "Leak Detected",
                "message": "Leak sensor triggered",
                "trigger_source": "leak_sensor",
                "trigger_value": {"leak": True},
                "threshold_value": {"leak": False},
                "evidence": {"leak_sensor": True},
                "device_id": "test-device",
                "created_at": datetime.now(timezone.utc).isoformat(),
            },
        )

        result = await provider.send(notification)

        assert result.success is True
        assert "CRITICAL" in result.provider_response["message"]
        assert "Leak Detected" in result.provider_response["message"]


class TestEmailNotificationProvider:
    """Tests for EmailNotificationProvider."""

    @pytest.fixture
    def provider(self):
        return EmailNotificationProvider({})

    def test_is_valid_email(self, provider):
        """Test email validation."""
        assert provider._is_valid_email("test@example.com") is True
        assert provider._is_valid_email("user.name@domain.org") is True
        assert provider._is_valid_email("invalid") is False
        assert provider._is_valid_email("@nodomain.com") is False
        assert provider._is_valid_email("noatdomain.com") is False

    @pytest.mark.asyncio
    async def test_send_missing_config(self, provider):
        """Test sending with missing SMTP config."""
        with patch("app.services.notification_providers.get_settings") as mock_settings:
            mock_settings.return_value.notifications.smtp_host = None

            notification = MockNotification(
                channel=NotificationChannel.EMAIL,
                provider="smtp",
                recipient="test@example.com",
            )

            result = await provider.send(notification)

            assert result.success is False
            assert result.error_category == NotificationErrorCategory.PERMANENT
            assert "not configured" in result.error_message

    @pytest.mark.asyncio
    async def test_send_invalid_recipient(self, provider):
        """Test sending with invalid email recipient."""
        with patch("app.services.notification_providers.get_settings") as mock_settings:
            mock_settings.return_value.notifications.smtp_host = "smtp.example.com"
            mock_settings.return_value.notifications.smtp_user = "user"
            mock_settings.return_value.notifications.smtp_password = "pass"

            notification = MockNotification(
                channel=NotificationChannel.EMAIL,
                provider="smtp",
                recipient="invalid-email",
            )

            result = await provider.send(notification)

            assert result.success is False
            assert result.error_category == NotificationErrorCategory.PERMANENT
            assert "Invalid email" in result.error_message


class TestWebhookNotificationProvider:
    """Tests for WebhookNotificationProvider."""

    @pytest.fixture
    def provider(self):
        return WebhookNotificationProvider({})

    def test_is_private_ip(self, provider):
        """Test private IP detection."""
        assert provider._is_private_ip("127.0.0.1") is True
        assert provider._is_private_ip("10.0.0.1") is True
        assert provider._is_private_ip("172.16.0.1") is True
        assert provider._is_private_ip("192.168.1.1") is True
        assert provider._is_private_ip("169.254.0.1") is True
        assert provider._is_private_ip("8.8.8.8") is False
        assert provider._is_private_ip("1.1.1.1") is False

        # IPv6
        assert provider._is_private_ip("::1") is True
        assert provider._is_private_ip("fe80::1") is True
        assert provider._is_private_ip("fc00::1") is True

    def test_validate_webhook_url_blocked_domains(self, provider):
        """Test URL validation blocks reserved domains."""
        with patch("app.services.notification_providers.get_settings") as mock_settings:
            mock_settings.return_value.is_production = True

            error = provider._validate_webhook_url("https://localhost/webhook")
            assert error is not None
            assert "Blocked domain" in error

            error = provider._validate_webhook_url("https://metadata.google.internal/webhook")
            assert error is not None

    def test_validate_webhook_url_http_in_production(self, provider):
        """Test URL validation requires HTTPS in production."""
        with patch("app.services.notification_providers.get_settings") as mock_settings:
            mock_settings.return_value.is_production = True

            error = provider._validate_webhook_url("http://example.com/webhook")
            assert error is not None
            assert "HTTPS" in error

            # HTTPS should be OK (but will fail on DNS resolution in test)
            with patch("socket.getaddrinfo") as mock_getaddrinfo:
                mock_getaddrinfo.return_value = [(2, 1, 6, "", ("93.184.216.34", 0))]
                error = provider._validate_webhook_url("https://example.com/webhook")
                assert error is None

    def test_validate_webhook_url_private_ip(self, provider):
        """Test URL validation blocks private IPs."""
        with patch("app.services.notification_providers.get_settings") as mock_settings:
            mock_settings.return_value.is_production = True

            with patch("socket.getaddrinfo") as mock_getaddrinfo:
                mock_getaddrinfo.return_value = [(2, 1, 6, "", ("10.0.0.1", 0))]
                error = provider._validate_webhook_url("https://internal.example.com/webhook")
                assert error is not None
                assert "private IP" in error

    @pytest.mark.asyncio
    async def test_send_blocked_url(self, provider):
        """Test sending to blocked URL."""
        notification = MockNotification(
            channel=NotificationChannel.WEBHOOK,
            provider="webhook",
            recipient="https://localhost/webhook",
        )

        result = await provider.send(notification)

        assert result.success is False
        assert result.error_category == NotificationErrorCategory.PERMANENT


class TestProviderFactory:
    """Tests for provider factory function."""

    def test_get_console_provider(self):
        provider = get_provider(NotificationChannel.CONSOLE)
        assert isinstance(provider, ConsoleNotificationProvider)

    def test_get_email_provider(self):
        provider = get_provider(NotificationChannel.EMAIL)
        assert isinstance(provider, EmailNotificationProvider)

    def test_get_webhook_provider(self):
        provider = get_provider(NotificationChannel.WEBHOOK)
        assert isinstance(provider, WebhookNotificationProvider)

    def test_get_invalid_provider(self):
        with pytest.raises(ValueError):
            get_provider("invalid_channel")


class TestNotificationService:
    """Tests for NotificationService."""

    @pytest.fixture
    def service(self, mock_db):
        return NotificationService(mock_db)

    @pytest.fixture
    def sample_alert(self):
        return MockAlert()

    @pytest.mark.asyncio
    async def test_create_notification(self, service, mock_db, sample_alert):
        """Test creating a notification."""
        # Mock db.execute to return no existing notification
        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=None)
        mock_db.execute = AsyncMock(return_value=mock_result)
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()
        mock_db.add = MagicMock()

        notification = await service.create_notification(
            alert=sample_alert,
            channel=NotificationChannel.CONSOLE,
            recipient="console",
            provider="console",
        )

        assert notification is not None
        assert notification.channel == NotificationChannel.CONSOLE
        assert notification.provider == "console"
        assert notification.recipient == "console"
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_duplicate_notification(self, service, mock_db, sample_alert):
        """Test creating duplicate notification returns None."""
        # Mock existing notification
        existing = MockNotification()
        mock_db.execute = AsyncMock()
        mock_db.execute.return_value.scalar_one_or_none.return_value = existing

        notification = await service.create_notification(
            alert=sample_alert,
            channel=NotificationChannel.CONSOLE,
            recipient="console",
            provider="console",
            dedupe_key="test-dedupe-key",
        )

        assert notification is None
        mock_db.add.assert_not_called()

    @pytest.mark.asyncio
    async def test_create_notifications_for_alert(self, service, mock_db, sample_alert):
        """Test creating notifications for all providers."""
        # Mock provider configs
        from app.models.notification import NotificationProviderConfig

        config = NotificationProviderConfig(
            id=uuid4(),
            device_id=sample_alert.device_id,
            channel=NotificationChannel.CONSOLE,
            provider="console",
            enabled=True,
            config={"recipient": "console"},
            min_severity="info",
        )

        # Mock execute to return provider configs
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [config]
        mock_result.scalars = MagicMock(return_value=mock_scalars)

        # Mock for duplicate check (returns None)
        mock_duplicate_result = MagicMock()
        mock_duplicate_result.scalar_one_or_none = MagicMock(return_value=None)

        # Mock for rate limit check
        mock_count_result = MagicMock()
        mock_count_result.scalar = MagicMock(return_value=0)

        call_count = [0]

        def execute_side_effect(query):
            call_count[0] += 1
            query_str = str(query).lower()
            if "notification_provider_config" in query_str:
                return mock_result
            elif "notification_outbox" in query_str and "dedupe_key" in query_str:
                # Duplicate check - return no existing
                mock_dup = MagicMock()
                mock_dup.scalar_one_or_none = MagicMock(return_value=None)
                return mock_dup
            elif "count" in query_str:
                return mock_count_result
            return mock_duplicate_result

        mock_db.execute = AsyncMock(side_effect=execute_side_effect)
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()
        mock_db.add = MagicMock()

        notifications = await service.create_notifications_for_alert(sample_alert)

        assert len(notifications) == 1
        assert notifications[0].channel == NotificationChannel.CONSOLE


class TestNotificationServiceRetryLogic:
    """Tests for notification retry logic."""

    @pytest.fixture
    def service(self, mock_db):
        return NotificationService(mock_db)

    @pytest.mark.asyncio
    async def test_deliver_notification_success(self, service, mock_db):
        """Test successful notification delivery."""
        notification = MockNotification(
            id=uuid4(),
            status=NotificationStatus.PENDING,
            channel=NotificationChannel.CONSOLE,
        )

        # Mock the provider send
        with patch("app.services.notification_service.get_provider") as mock_get_provider:
            mock_provider = AsyncMock()
            mock_provider.send = AsyncMock(
                return_value=NotificationResult(
                    success=True,
                    provider_response={"logged": True},
                )
            )
            mock_get_provider.return_value = mock_provider

            mock_db.commit = AsyncMock()
            mock_db.refresh = AsyncMock()

            result = await service._deliver_notification(notification)

            assert result.success is True
            assert notification.status == NotificationStatus.SENT
            assert notification.sent_at is not None

    @pytest.mark.asyncio
    async def test_deliver_notification_retry(self, service, mock_db):
        """Test notification retry on failure."""
        notification = MockNotification(
            id=uuid4(),
            status=NotificationStatus.PENDING,
            attempt_count=0,
            max_attempts=3,
            channel=NotificationChannel.CONSOLE,
        )

        with patch("app.services.notification_service.get_provider") as mock_get_provider:
            mock_provider = AsyncMock()
            mock_provider.send = AsyncMock(
                return_value=NotificationResult(
                    success=False,
                    error_category=NotificationErrorCategory.TRANSIENT,
                    error_message="Connection timeout",
                )
            )
            mock_get_provider.return_value = mock_provider

            mock_db.commit = AsyncMock()
            mock_db.refresh = AsyncMock()

            result = await service._deliver_notification(notification)

            assert result.success is False
            assert notification.status == NotificationStatus.RETRY
            assert notification.attempt_count == 1
            assert notification.next_attempt_at is not None

    @pytest.mark.asyncio
    async def test_deliver_notification_dead_letter(self, service, mock_db):
        """Test notification goes to dead letter after max attempts."""
        notification = MockNotification(
            id=uuid4(),
            status=NotificationStatus.RETRY,
            attempt_count=4,
            max_attempts=5,
            channel=NotificationChannel.CONSOLE,
        )

        with patch("app.services.notification_service.get_provider") as mock_get_provider:
            mock_provider = AsyncMock()
            mock_provider.send = AsyncMock(
                return_value=NotificationResult(
                    success=False,
                    error_category=NotificationErrorCategory.TRANSIENT,
                    error_message="Connection timeout",
                )
            )
            mock_get_provider.return_value = mock_provider

            mock_db.commit = AsyncMock()
            mock_db.refresh = AsyncMock()

            result = await service._deliver_notification(notification)

            assert result.success is False
            assert notification.status == NotificationStatus.DEAD_LETTER
            assert notification.attempt_count == 5


class TestNotificationTemplates:
    """Tests for default notification templates."""

    def test_default_templates_exist(self):
        """Test that default templates exist for all critical alert types."""
        provider = ConsoleNotificationProvider({})
        templates = provider._get_default_templates()

        assert "default" in templates
        assert "leak_detected" in templates
        assert "pressure_high" in templates
        assert "pump_overcurrent" in templates
        assert "water_quality_degraded" in templates
        assert "filter_health_critical" in templates

    def test_template_rendering(self):
        """Test template rendering with data."""
        provider = ConsoleNotificationProvider({})
        template_data = {
            "alert_code": "leak_detected",
            "severity": "critical",
            "title": "Leak Detected",
            "message": "Water leak detected in kitchen",
            "trigger_source": "leak_sensor",
            "trigger_value": {"leak": True},
            "threshold_value": {"leak": False},
            "evidence": {"leak_sensor": True, "location": "kitchen"},
            "device_id": "device-123",
            "created_at": "2024-01-15T10:30:00Z",
        }

        subject, body = provider.render_template("leak_detected", template_data)

        assert "Leak Detected" in subject
        assert "CRITICAL" in body
        assert "device-123" in body
        assert "Water leak detected" in body
        assert "IMMEDIATE ACTION REQUIRED" in body


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
