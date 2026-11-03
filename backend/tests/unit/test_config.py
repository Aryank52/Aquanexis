"""
Tests for configuration management.
"""

import pytest
from pydantic import ValidationError

from app.infrastructure.config import (
    AppSettings,
    DatabaseSettings,
    AuthSettings,
    MLSettings,
    SafetySettings,
)


class TestDatabaseSettings:
    """Tests for database settings."""

    def test_default_values(self):
        """Test default database settings."""
        # Use explicit values to avoid environment variable interference
        db = DatabaseSettings(
            host="localhost",
            port=5432,
            user="aquanexis",
            password="aquanexis",
            name="aquanexis",
            pool_size=20,
        )
        assert db.host == "localhost"
        assert db.port == 5432
        assert db.user == "aquanexis"
        assert db.password == "aquanexis"
        assert db.name == "aquanexis"
        assert db.pool_size == 20

    def test_url_property(self):
        """Test computed URL property."""
        db = DatabaseSettings(
            host="db.example.com",
            port=5433,
            user="test",
            password="secret",
            name="testdb",
        )
        url = str(db.url)
        # Pydantic PostgresDsn may include double slash before path
        assert "test:secret@db.example.com:5433" in url
        assert "testdb" in url

    def test_sync_url_property(self):
        """Test synchronous URL for migrations."""
        db = DatabaseSettings(
            host="localhost",
            user="test",
            password="secret",
            name="testdb",
        )
        sync_url = db.sync_url
        assert sync_url == "postgresql://test:secret@localhost:5432/testdb"


class TestAuthSettings:
    """Tests for authentication settings."""

    def test_valid_secret(self):
        """Test valid JWT secret (min 32 chars)."""
        auth = AuthSettings(
            device_jwt_secret="a" * 32,
            api_key_salt="b" * 16,
        )
        assert auth.device_jwt_secret == "a" * 32
        assert auth.device_jwt_algorithm == "HS256"

    def test_invalid_secret_too_short(self):
        """Test that short secrets are rejected."""
        with pytest.raises(ValidationError):
            AuthSettings(
                device_jwt_secret="short",
                api_key_salt="b" * 16,
            )

    def test_invalid_salt_too_short(self):
        """Test that short API key salts are rejected."""
        with pytest.raises(ValidationError):
            AuthSettings(
                device_jwt_secret="a" * 32,
                api_key_salt="short",
            )


class TestMLSettings:
    """Tests for ML settings."""

    def test_defaults(self):
        """Test default ML settings."""
        ml = MLSettings()
        assert ml.enabled is True
        assert ml.artifact_dir == "/app/models"
        assert ml.anomaly_window_minutes == 15
        assert ml.rul_model_name == "baseline_v1"


class TestSafetySettings:
    """Tests for safety settings."""

    def test_defaults(self):
        """Test default safety settings."""
        safety = SafetySettings()
        assert safety.enabled is True
        assert safety.action_timeout_seconds == 5
        assert safety.default_leak_action == "close_inlet_valve"
        assert safety.default_pressure_max_kpa == 600.0


class TestAppSettings:
    """Tests for main app settings."""

    def test_development_env(self):
        """Test development environment detection."""
        settings = AppSettings(env="development")
        assert settings.is_development is True
        assert settings.is_production is False

    def test_production_env(self):
        """Test production environment detection."""
        settings = AppSettings(env="production")
        assert settings.is_development is False
        assert settings.is_production is True

    def test_staging_env(self):
        """Test staging environment."""
        settings = AppSettings(env="staging")
        assert settings.is_development is False
        assert settings.is_production is False

    def test_invalid_env(self):
        """Test invalid environment rejected."""
        with pytest.raises(ValidationError):
            AppSettings(env="invalid")

    def test_nested_settings(self):
        """Test nested settings are properly initialized."""
        settings = AppSettings()
        assert isinstance(settings.database, DatabaseSettings)
        assert isinstance(settings.auth, AuthSettings)
        assert isinstance(settings.ml, MLSettings)
        assert isinstance(settings.safety, SafetySettings)

    def test_allowed_origins(self):
        """Test CORS origins parsing."""
        settings = AppSettings(allowed_origins=["http://localhost:3000", "https://app.example.com"])
        assert len(settings.allowed_origins) == 2
        assert "http://localhost:3000" in settings.allowed_origins
