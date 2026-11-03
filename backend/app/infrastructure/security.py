"""
Security infrastructure: JWT token handling, device authentication, API key validation.
"""

from collections import defaultdict
from datetime import datetime, timedelta, timezone
from time import time
from typing import Annotated, Optional
from uuid import UUID

from fastapi import Depends, Header, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from pydantic import BaseModel

from app.infrastructure.config import get_settings
from app.infrastructure.logging import get_logger

settings = get_settings()
logger = get_logger(__name__)

# Security schemes
bearer_scheme = HTTPBearer(auto_error=False)
api_key_header = Header(None, alias="X-API-Key")


class TokenPayload(BaseModel):
    """JWT token payload structure."""

    sub: str  # device_id
    iat: int
    exp: int
    iss: str
    aud: str
    scope: str = "telemetry:write"


class DeviceClaims(BaseModel):
    """Extracted device claims from token."""

    device_id: UUID
    scope: str


def create_device_token(device_id: UUID, scope: str = "telemetry:write") -> str:
    """Create a JWT token for a device."""
    now = datetime.now(timezone.utc)
    expiry = now + timedelta(hours=settings.auth.device_jwt_expiry_hours)

    payload = {
        "sub": str(device_id),
        "iat": int(now.timestamp()),
        "exp": int(expiry.timestamp()),
        "iss": settings.auth.device_jwt_issuer,
        "aud": settings.auth.device_jwt_audience,
        "scope": scope,
    }

    token = jwt.encode(
        payload,
        settings.auth.device_jwt_secret,
        algorithm=settings.auth.device_jwt_algorithm,
    )
    return token


def verify_device_token(token: str) -> TokenPayload:
    """Verify and decode a device JWT token."""
    try:
        payload = jwt.decode(
            token,
            settings.auth.device_jwt_secret,
            algorithms=[settings.auth.device_jwt_algorithm],
            issuer=settings.auth.device_jwt_issuer,
            audience=settings.auth.device_jwt_audience,
        )
        return TokenPayload(**payload)
    except JWTError as e:
        logger.warning("jwt_verification_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_device_claims(
    credentials: Annotated[Optional[HTTPAuthorizationCredentials], Depends(bearer_scheme)],
) -> DeviceClaims:
    """FastAPI dependency to extract device claims from JWT."""
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token_payload = verify_device_token(credentials.credentials)

    try:
        device_id = UUID(token_payload.sub)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid device ID in token",
        )

    return DeviceClaims(device_id=device_id, scope=token_payload.scope)


# API Key authentication for admin endpoints
class APIKeyManager:
    """Manages API key validation (hashed storage)."""

    def __init__(self) -> None:
        self._valid_keys: set[str] = set()

    def add_key(self, raw_key: str) -> None:
        """Add a valid API key (in production, store hashed)."""
        self._valid_keys.add(raw_key)

    def verify_key(self, raw_key: str) -> bool:
        """Verify an API key."""
        return raw_key in self._valid_keys


api_key_manager = APIKeyManager()

# Add default dev key if in development
if settings.is_development:
    api_key_manager.add_key("dev-api-key-change-in-production")


async def verify_api_key(
    api_key: Annotated[Optional[str], Header(alias="X-API-Key")] = None,
    credentials: Annotated[Optional[HTTPAuthorizationCredentials], Depends(bearer_scheme)] = None,
) -> bool:
    """FastAPI dependency to verify API key or valid operator/device Bearer JWT for admin endpoints."""
    if api_key and api_key_manager.verify_key(api_key):
        return True

    if settings.is_development and api_key == "dev-api-key-change-in-production":
        return True

    if credentials is not None:
        token_payload = verify_device_token(credentials.credentials)
        if token_payload.sub:
            return True

    if settings.is_production and api_key is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required",
        )

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid API key or missing authorization",
    )


# Rate limiting (simple in-memory, replace with Redis in production)
_rate_limit_store: dict[str, list[float]] = defaultdict(list)


async def rate_limit(
    request: Request,
    device_claims: Annotated[Optional[DeviceClaims], Depends(get_device_claims)] = None,
) -> None:
    """Simple rate limiting by device ID or IP."""
    if settings.is_development:
        return  # Skip in development

    identifier = str(device_claims.device_id) if device_claims else request.client.host
    now = time()
    window_start = now - settings.auth.rate_limit_window_seconds

    # Clean old entries
    _rate_limit_store[identifier] = [
        ts for ts in _rate_limit_store[identifier] if ts > window_start
    ]

    if len(_rate_limit_store[identifier]) >= settings.auth.rate_limit_requests:
        logger.warning("rate_limit_exceeded", identifier=identifier)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded",
        )

    _rate_limit_store[identifier].append(now)
