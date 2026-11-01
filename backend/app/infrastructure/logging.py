"""
Structured logging configuration using structlog.
Provides JSON output with request correlation IDs.
"""
import logging
import sys
from typing import Any, Callable, Optional

import structlog
from structlog.types import EventDict, WrappedLogger

from app.infrastructure.config import get_settings

settings = get_settings()


def add_request_id(logger: WrappedLogger, method_name: str, event_dict: EventDict) -> EventDict:
    """Add request ID from contextvars if available."""
    try:
        from contextvars import ContextVar
        request_id_var: ContextVar[str] = ContextVar("request_id", default="")
        request_id = request_id_var.get()
        if request_id:
            event_dict["request_id"] = request_id
    except (ImportError, LookupError):
        pass
    return event_dict


def add_service_context(logger: WrappedLogger, method_name: str, event_dict: EventDict) -> EventDict:
    """Add service context to all log entries."""
    event_dict["service"] = "aquanexis-backend"
    event_dict["environment"] = settings.env
    return event_dict


def drop_color_message_key(logger: WrappedLogger, method_name: str, event_dict: EventDict) -> EventDict:
    """Remove color_message key if present (from console renderer)."""
    event_dict.pop("color_message", None)
    return event_dict


def configure_logging() -> None:
    """Configure structlog for the application."""
    log_level = getattr(logging, settings.logging.level.upper(), logging.INFO)

    # Standard library logging config
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=log_level,
    )

    # Configure structlog
    shared_processors: list[Callable[[WrappedLogger, str, EventDict], EventDict]] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        add_service_context,
        add_request_id,
        drop_color_message_key,
    ]

    if settings.logging.format == "json":
        # JSON output for production
        processors = shared_processors + [
            structlog.processors.JSONRenderer(),
        ]
    else:
        # Human-readable console output for development
        processors = shared_processors + [
            structlog.dev.ConsoleRenderer(colors=True),
        ]

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Set log levels for noisy libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)


def get_logger(name: Optional[str] = None) -> structlog.stdlib.BoundLogger:
    """Get a structured logger instance."""
    return structlog.get_logger(name)


# Request ID context variable for middleware
from contextvars import ContextVar
request_id_var: ContextVar[str] = ContextVar("request_id", default="")

def set_request_id(request_id: str) -> None:
    """Set request ID in contextvars."""
    request_id_var.set(request_id)

def get_request_id() -> str:
    """Get current request ID."""
    return request_id_var.get("")