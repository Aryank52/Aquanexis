"""
Notification provider abstraction and implementations.
"""

import abc
import re
import smtplib
import socket
import ssl
from dataclasses import dataclass
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any, Dict, Optional
from urllib.parse import urlparse

import httpx
from jinja2 import BaseLoader, Environment, select_autoescape

from app.infrastructure.config import get_settings
from app.infrastructure.logging import get_logger
from app.models.notification import (
    NotificationChannel,
    NotificationErrorCategory,
    NotificationOutbox,
)

logger = get_logger(__name__)


# Jinja2 environment for templates
template_env = Environment(
    loader=BaseLoader(),
    autoescape=select_autoescape(["html", "xml"]),
    trim_blocks=True,
    lstrip_blocks=True,
)


@dataclass
class NotificationResult:
    """Result of a notification send attempt."""

    success: bool
    error_category: Optional[NotificationErrorCategory] = None
    error_message: Optional[str] = None
    provider_response: Optional[Dict[str, Any]] = None


class BaseNotificationProvider(abc.ABC):
    """Abstract base class for notification providers."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.channel = self._get_channel()

    @abc.abstractmethod
    def _get_channel(self) -> NotificationChannel:
        """Return the notification channel this provider handles."""
        pass

    @abc.abstractmethod
    async def send(self, notification: NotificationOutbox) -> NotificationResult:
        """Send a notification. Returns result with success status and error info."""
        pass

    def render_template(self, template_name: str, template_data: Dict[str, Any]) -> tuple[str, str]:
        """Render subject and body from template."""
        # Default templates if not in database
        default_templates = self._get_default_templates()

        if template_name in default_templates:
            template = default_templates[template_name]
            subject_tmpl = template_env.from_string(template.get("subject", ""))
            body_tmpl = template_env.from_string(template["body"])
        else:
            # Fallback to generic template
            subject_tmpl = template_env.from_string("AquaNexis Alert: {{ alert_code }}")
            body_tmpl = template_env.from_string(default_templates["default"]["body"])

        subject = subject_tmpl.render(**template_data) if subject_tmpl else ""
        body = body_tmpl.render(**template_data)

        return subject, body

    def _get_default_templates(self) -> Dict[str, Dict[str, str]]:
        """Get default templates for this provider."""
        return {
            "default": {
                "subject": "AquaNexis Alert: {{ alert_code }}",
                "body": """
Alert: {{ title }}
Severity: {{ severity }}
Device: {{ device_id }}
Time: {{ created_at }}

{{ message }}

Trigger: {{ trigger_source }}
Value: {{ trigger_value }}
Threshold: {{ threshold_value }}

Evidence: {{ evidence }}
                """.strip(),
            },
            "leak_detected": {
                "subject": "🚨 CRITICAL: Leak Detected - Device {{ device_id }}",
                "body": """
CRITICAL ALERT: Water leak detected!

Device: {{ device_id }}
Time: {{ created_at }}

{{ message }}

IMMEDIATE ACTION REQUIRED: Check the device location for water accumulation.
The system may have automatically closed the inlet valve.

Trigger: {{ trigger_source }}
Evidence: {{ evidence }}
                """.strip(),
            },
            "pressure_high": {
                "subject": "🚨 CRITICAL: High Pressure - Device {{ device_id }}",
                "body": """
CRITICAL ALERT: Excessive pressure detected!

Device: {{ device_id }}
Time: {{ created_at }}

{{ message }}

The system may have automatically opened the relief valve or stopped the pump.

Trigger: {{ trigger_source }}
Value: {{ trigger_value }}
Threshold: {{ threshold_value }}
                """.strip(),
            },
            "pump_overcurrent": {
                "subject": "🚨 CRITICAL: Pump Overcurrent - Device {{ device_id }}",
                "body": """
CRITICAL ALERT: Pump overcurrent detected!

Device: {{ device_id }}
Time: {{ created_at }}

{{ message }}

The system may have automatically stopped the pump to prevent damage.

Trigger: {{ trigger_source }}
Value: {{ trigger_value }}
Threshold: {{ threshold_value }}
                """.strip(),
            },
            "water_quality_degraded": {
                "subject": "⚠️ WARNING: Water Quality Degraded - Device {{ device_id }}",
                "body": """
WARNING: Water quality has degraded.

Device: {{ device_id }}
Time: {{ created_at }}

{{ message }}

Trigger: {{ trigger_source }}
Value: {{ trigger_value }}
Threshold: {{ threshold_value }}

Consider checking or replacing filters.
                """.strip(),
            },
            "filter_health_critical": {
                "subject": "🚨 CRITICAL: Filter Health Critical - Device {{ device_id }}",
                "body": """
CRITICAL ALERT: Filter health is critical!

Device: {{ device_id }}
Time: {{ created_at }}

{{ message }}

Filter replacement is urgently required.

Trigger: {{ trigger_source }}
Value: {{ trigger_value }}
Threshold: {{ threshold_value }}
                """.strip(),
            },
        }


class ConsoleNotificationProvider(BaseNotificationProvider):
    """Console/logging notification provider for development."""

    def _get_channel(self) -> NotificationChannel:
        return NotificationChannel.CONSOLE

    async def send(self, notification: NotificationOutbox) -> NotificationResult:
        """Log the notification to console."""
        try:
            subject, body = self.render_template(
                notification.template_name or "default", notification.template_data or {}
            )

            log_message = f"""
{"=" * 60}
NOTIFICATION [{notification.channel.value.upper()}] - {notification.status.value.upper()}
Alert ID: {notification.alert_id}
Device ID: {notification.device_id}
Subject: {subject}
Recipient: {notification.recipient}
Attempt: {notification.attempt_count + 1}/{notification.max_attempts}
{"=" * 60}
{body}
{"=" * 60}
            """.strip()

            logger.info(log_message)

            return NotificationResult(
                success=True,
                provider_response={"logged": True, "message": log_message},
            )
        except Exception as e:
            logger.error(f"Console notification failed: {e}")
            return NotificationResult(
                success=False,
                error_category=NotificationErrorCategory.TRANSIENT,
                error_message=str(e),
            )


class EmailNotificationProvider(BaseNotificationProvider):
    """SMTP email notification provider."""

    def _get_channel(self) -> NotificationChannel:
        return NotificationChannel.EMAIL

    def _validate_config(self) -> Optional[str]:
        """Validate email configuration. Returns error message if invalid."""
        settings = get_settings()
        if not settings.notifications.smtp_host:
            return "SMTP host not configured"
        if not settings.notifications.smtp_user:
            return "SMTP user not configured"
        if not settings.notifications.smtp_password:
            return "SMTP password not configured"
        return None

    async def send(self, notification: NotificationOutbox) -> NotificationResult:
        """Send email notification via SMTP."""
        # Validate config
        config_error = self._validate_config()
        if config_error:
            return NotificationResult(
                success=False,
                error_category=NotificationErrorCategory.PERMANENT,
                error_message=config_error,
            )

        # Validate recipient is an email
        if not self._is_valid_email(notification.recipient):
            return NotificationResult(
                success=False,
                error_category=NotificationErrorCategory.PERMANENT,
                error_message=f"Invalid email address: {notification.recipient}",
            )

        settings = get_settings()

        try:
            subject, body = self.render_template(
                notification.template_name or "default", notification.template_data or {}
            )

            # Create message
            msg = MIMEMultipart()
            msg["From"] = settings.notifications.smtp_from
            msg["To"] = notification.recipient
            msg["Subject"] = subject or notification.subject or "AquaNexis Alert"

            # Add both plain text and HTML versions
            msg.attach(MIMEText(body, "plain"))

            # HTML version
            html_body = body.replace("\n", "<br>")
            html_body = f"<pre style='font-family: monospace;'>{html_body}</pre>"
            msg.attach(MIMEText(html_body, "html"))

            # Send via SMTP
            context = ssl.create_default_context()

            with smtplib.SMTP(
                settings.notifications.smtp_host, settings.notifications.smtp_port
            ) as server:
                server.starttls(context=context)
                server.login(settings.notifications.smtp_user, settings.notifications.smtp_password)
                server.send_message(msg)

            logger.info(
                "email_notification_sent",
                alert_id=str(notification.alert_id),
                device_id=str(notification.device_id),
                recipient=notification.recipient,
            )

            return NotificationResult(
                success=True,
                provider_response={"sent_to": notification.recipient},
            )

        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"SMTP authentication failed: {e}")
            return NotificationResult(
                success=False,
                error_category=NotificationErrorCategory.PERMANENT,
                error_message=f"SMTP authentication failed: {e}",
            )
        except smtplib.SMTPRecipientsRefused as e:
            logger.error(f"SMTP recipient refused: {e}")
            return NotificationResult(
                success=False,
                error_category=NotificationErrorCategory.PERMANENT,
                error_message=f"Recipient refused: {e}",
            )
        except (smtplib.SMTPConnectError, socket.timeout, socket.gaierror) as e:
            logger.warning(f"SMTP connection error (transient): {e}")
            return NotificationResult(
                success=False,
                error_category=NotificationErrorCategory.TRANSIENT,
                error_message=f"Connection error: {e}",
            )
        except Exception as e:
            logger.error(f"Email notification failed: {e}")
            return NotificationResult(
                success=False,
                error_category=NotificationErrorCategory.UNKNOWN,
                error_message=str(e),
            )

    def _is_valid_email(self, email: str) -> bool:
        """Basic email validation."""
        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        return bool(re.match(pattern, email))


class WebhookNotificationProvider(BaseNotificationProvider):
    """Webhook notification provider with SSRF protection."""

    def _get_channel(self) -> NotificationChannel:
        return NotificationChannel.WEBHOOK

    # Private IP ranges to block (SSRF protection)
    BLOCKED_NETWORKS = [
        "127.0.0.0/8",  # Loopback
        "10.0.0.0/8",  # Private Class A
        "172.16.0.0/12",  # Private Class B
        "192.168.0.0/16",  # Private Class C
        "169.254.0.0/16",  # Link-local
        "::1/128",  # IPv6 loopback
        "fe80::/10",  # IPv6 link-local
        "fc00::/7",  # IPv6 unique local
    ]

    # Reserved/special domains to block
    BLOCKED_DOMAINS = {
        "localhost",
        "localhost.localdomain",
        "metadata.google.internal",
        "169.254.169.254",  # AWS metadata
        "metadata.azure.com",
        "metadata.packet.net",
    }

    def _validate_webhook_url(self, url: str) -> Optional[str]:
        """Validate webhook URL for SSRF protection. Returns error message if invalid."""
        try:
            parsed = urlparse(url)

            # Must be HTTPS in production
            settings = get_settings()
            if settings.is_production and parsed.scheme != "https":
                return "Webhook URL must use HTTPS in production"

            if parsed.scheme not in ("http", "https"):
                return "Webhook URL must use HTTP or HTTPS"

            hostname = parsed.hostname
            if not hostname:
                return "Invalid hostname"

            # Block localhost and reserved domains
            if hostname.lower() in self.BLOCKED_DOMAINS:
                return f"Blocked domain: {hostname}"

            # Resolve hostname and check IP
            try:
                ips = socket.getaddrinfo(hostname, None)
                for ip_info in ips:
                    ip = ip_info[4][0]
                    if self._is_private_ip(ip):
                        return f"Blocked private IP: {ip}"
            except socket.gaierror:
                return f"Cannot resolve hostname: {hostname}"

            # Check for redirect-prone URLs
            if parsed.port and parsed.port in (22, 23, 25, 53, 110, 143, 993, 995):
                return "Blocked port"

            return None

        except Exception as e:
            return f"URL validation failed: {e}"

    def _is_private_ip(self, ip: str) -> bool:
        """Check if IP is in private/reserved ranges."""
        try:
            import ipaddress

            ip_obj = ipaddress.ip_address(ip)

            # Check private ranges
            private_networks = [
                ipaddress.ip_network("127.0.0.0/8"),
                ipaddress.ip_network("10.0.0.0/8"),
                ipaddress.ip_network("172.16.0.0/12"),
                ipaddress.ip_network("192.168.0.0/16"),
                ipaddress.ip_network("169.254.0.0/16"),
                ipaddress.ip_network("::1/128"),
                ipaddress.ip_network("fe80::/10"),
                ipaddress.ip_network("fc00::/7"),
            ]

            for network in private_networks:
                if ip_obj in network:
                    return True

            # Check reserved
            return ip_obj.is_reserved or ip_obj.is_loopback or ip_obj.is_link_local
        except Exception:
            return True  # If we can't parse, assume unsafe

    async def send(self, notification: NotificationOutbox) -> NotificationResult:
        """Send webhook notification with SSRF protection."""
        # Validate webhook URL
        validation_error = self._validate_webhook_url(notification.recipient)
        if validation_error:
            logger.warning(
                "webhook_url_blocked",
                alert_id=str(notification.alert_id),
                device_id=str(notification.device_id),
                url=notification.recipient,
                reason=validation_error,
            )
            return NotificationResult(
                success=False,
                error_category=NotificationErrorCategory.PERMANENT,
                error_message=validation_error,
            )

        try:
            subject, body = self.render_template(
                notification.template_name or "default", notification.template_data or {}
            )

            # Prepare webhook payload
            payload = {
                "alert_id": str(notification.alert_id),
                "device_id": str(notification.device_id),
                "subject": subject or notification.subject,
                "body": body,
                "channel": notification.channel.value,
                "template": notification.template_name,
                "data": notification.template_data,
            }

            # Prepare headers
            headers = {
                "Content-Type": "application/json",
                "User-Agent": "AquaNexis-Webhook/1.0",
            }

            # Add signature if secret configured
            settings = get_settings()
            if settings.notifications.webhook_secret:
                import hashlib
                import hmac
                import json

                body_bytes = json.dumps(payload, sort_keys=True).encode()
                signature = hmac.new(
                    settings.notifications.webhook_secret.encode(), body_bytes, hashlib.sha256
                ).hexdigest()
                headers["X-AquaNexis-Signature"] = f"sha256={signature}"

            # Send with timeout
            timeout = httpx.Timeout(10.0, connect=5.0)
            async with httpx.AsyncClient(timeout=timeout, follow_redirects=False) as client:
                response = await client.post(
                    notification.recipient,
                    json=payload,
                    headers=headers,
                )
                response.raise_for_status()

            logger.info(
                "webhook_notification_sent",
                alert_id=str(notification.alert_id),
                device_id=str(notification.device_id),
                url=notification.recipient,
                status_code=response.status_code,
            )

            return NotificationResult(
                success=True,
                provider_response={
                    "status_code": response.status_code,
                    "url": notification.recipient,
                },
            )

        except httpx.TimeoutException as e:
            logger.warning(f"Webhook timeout: {e}")
            return NotificationResult(
                success=False,
                error_category=NotificationErrorCategory.TRANSIENT,
                error_message=f"Webhook timeout: {e}",
            )
        except httpx.HTTPStatusError as e:
            # 4xx = permanent, 5xx = transient
            if 400 <= e.response.status_code < 500:
                error_cat = NotificationErrorCategory.PERMANENT
            else:
                error_cat = NotificationErrorCategory.TRANSIENT
            logger.warning(f"Webhook HTTP error: {e}")
            return NotificationResult(
                success=False,
                error_category=error_cat,
                error_message=f"HTTP {e.response.status_code}: {e}",
            )
        except httpx.RequestError as e:
            logger.warning(f"Webhook request error: {e}")
            return NotificationResult(
                success=False,
                error_category=NotificationErrorCategory.TRANSIENT,
                error_message=f"Request error: {e}",
            )
        except Exception as e:
            logger.error(f"Webhook notification failed: {e}")
            return NotificationResult(
                success=False,
                error_category=NotificationErrorCategory.UNKNOWN,
                error_message=str(e),
            )


def get_provider(
    channel: NotificationChannel, config: Optional[Dict[str, Any]] = None
) -> BaseNotificationProvider:
    """Factory function to get notification provider by channel."""
    providers = {
        NotificationChannel.CONSOLE: ConsoleNotificationProvider,
        NotificationChannel.EMAIL: EmailNotificationProvider,
        NotificationChannel.WEBHOOK: WebhookNotificationProvider,
    }

    provider_class = providers.get(channel)
    if not provider_class:
        raise ValueError(f"No provider for channel: {channel}")

    return provider_class(config or {})
