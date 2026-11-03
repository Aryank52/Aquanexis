"""
Tests for security infrastructure.
"""

import pytest
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from jose import jwt

from app.infrastructure.security import (
    create_device_token,
    verify_device_token,
    TokenPayload,
    api_key_manager,
)
from app.infrastructure.config import settings


class TestDeviceJWT:
    """Tests for device JWT token creation and verification."""

    def test_create_device_token(self):
        """Test creating a device token."""
        device_id = uuid4()
        token = create_device_token(device_id)

        assert isinstance(token, str)
        assert len(token) > 0

        # Decode without verification to check payload
        payload = jwt.decode(
            token,
            settings.auth.device_jwt_secret,
            algorithms=[settings.auth.device_jwt_algorithm],
            options={"verify_signature": False, "verify_aud": False},
        )
        assert payload["sub"] == str(device_id)
        assert payload["iss"] == settings.auth.device_jwt_issuer
        assert payload["aud"] == settings.auth.device_jwt_audience
        assert payload["scope"] == "telemetry:write"
        assert "iat" in payload
        assert "exp" in payload

    def test_token_expiry(self):
        """Test token has correct expiry."""
        device_id = uuid4()
        token = create_device_token(device_id)

        payload = jwt.decode(
            token,
            settings.auth.device_jwt_secret,
            algorithms=[settings.auth.device_jwt_algorithm],
            options={"verify_signature": False, "verify_aud": False},
        )

        exp = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
        iat = datetime.fromtimestamp(payload["iat"], tz=timezone.utc)
        expected_exp = iat + timedelta(hours=settings.auth.device_jwt_expiry_hours)

        # Allow 1 second tolerance
        assert abs((exp - expected_exp).total_seconds()) < 1

    def test_verify_valid_token(self):
        """Test verifying a valid token."""
        device_id = uuid4()
        token = create_device_token(device_id)

        payload = verify_device_token(token)

        assert isinstance(payload, TokenPayload)
        assert payload.sub == str(device_id)
        assert payload.scope == "telemetry:write"

    def test_verify_expired_token(self):
        """Test that expired tokens are rejected."""
        device_id = uuid4()
        # Create token with past expiry
        past = datetime.now(timezone.utc) - timedelta(hours=1)
        payload = {
            "sub": str(device_id),
            "iat": int(past.timestamp()),
            "exp": int(past.timestamp()),
            "iss": settings.auth.device_jwt_issuer,
            "aud": settings.auth.device_jwt_audience,
            "scope": "telemetry:write",
        }
        expired_token = jwt.encode(
            payload,
            settings.auth.device_jwt_secret,
            algorithm=settings.auth.device_jwt_algorithm,
        )

        with pytest.raises(Exception) as exc_info:
            verify_device_token(expired_token)
        assert (
            "expired" in str(exc_info.value).lower() or "signature" in str(exc_info.value).lower()
        )

    def test_verify_invalid_signature(self):
        """Test that tokens with wrong secret are rejected."""
        device_id = uuid4()
        token = create_device_token(device_id)

        # Try to verify with wrong secret
        wrong_secret = "wrong-secret-minimum-32-characters-long"
        payload = jwt.decode(
            token,
            wrong_secret,
            algorithms=[settings.auth.device_jwt_algorithm],
            options={"verify_signature": False, "verify_aud": False},
        )
        # Re-encode with wrong secret
        wrong_token = jwt.encode(
            payload,
            wrong_secret,
            algorithm=settings.auth.device_jwt_algorithm,
        )

        with pytest.raises(Exception):
            verify_device_token(wrong_token)

    def test_verify_malformed_token(self):
        """Test that malformed tokens are rejected."""
        with pytest.raises(Exception):
            verify_device_token("not.a.valid.token")

    def test_custom_scope(self):
        """Test creating token with custom scope."""
        device_id = uuid4()
        token = create_device_token(device_id, scope="admin:all")

        payload = verify_device_token(token)
        assert payload.scope == "admin:all"


class TestAPIKeyManager:
    """Tests for API key management."""

    def test_add_and_verify_key(self):
        """Test adding and verifying API keys."""
        key = "test-api-key-12345"
        api_key_manager.add_key(key)

        assert api_key_manager.verify_key(key) is True
        assert api_key_manager.verify_key("wrong-key") is False

    def test_dev_key_in_development(self):
        """Test dev key works in development."""
        # Settings is already in test mode (development)
        assert api_key_manager.verify_key("dev-api-key-change-in-production") is True
