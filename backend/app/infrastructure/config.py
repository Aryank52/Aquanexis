"""
Application configuration using Pydantic Settings v2.
All settings loaded from environment variables with validation.
"""
from functools import lru_cache
from typing import List, Optional, Union
from pydantic import AliasChoices, Field, PostgresDsn, computed_field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseSettings(BaseSettings):
    """Database connection settings."""
    model_config = SettingsConfigDict(env_prefix="DB_", extra="ignore")

    host: str = "localhost"
    port: int = 5432
    user: str = "aquanexis"
    password: str = "aquanexis"
    name: str = "aquanexis"
    pool_size: int = 20
    max_overflow: int = 10
    pool_timeout: int = 30
    pool_recycle: int = 3600
    echo: bool = False

    @computed_field
    @property
    def url(self) -> PostgresDsn:
        return PostgresDsn.build(
            scheme="postgresql+asyncpg",
            username=self.user,
            password=self.password,
            host=self.host,
            port=self.port,
            path=self.name,
        )

    @computed_field
    @property
    def sync_url(self) -> str:
        """Synchronous URL for Alembic migrations."""
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"


class AuthSettings(BaseSettings):
    """Authentication and authorization settings."""
    model_config = SettingsConfigDict(env_prefix="AUTH_", extra="ignore")

    device_jwt_secret: str = Field(
        default="test-secret-minimum-32-characters-long-for-testing-only",
        min_length=32,
        validation_alias=AliasChoices("device_jwt_secret", "AUTH_DEVICE_JWT_SECRET", "DEVICE_JWT_SECRET"),
    )
    device_jwt_algorithm: str = "HS256"
    device_jwt_expiry_hours: int = 24
    device_jwt_issuer: str = "aquanexis"
    device_jwt_audience: str = "aquanexis-devices"

    api_key_salt: str = Field(
        default="test-salt-for-testing-only",
        min_length=16,
        validation_alias=AliasChoices("api_key_salt", "AUTH_API_KEY_SALT", "API_KEY_SALT"),
    )
    api_key_prefix: str = "ak_"
    rate_limit_requests: int = 1000
    rate_limit_window_seconds: int = 60


class MLSettings(BaseSettings):
    """Machine learning settings."""
    model_config = SettingsConfigDict(env_prefix="ML_")

    enabled: bool = True
    artifact_dir: str = "/app/models"
    anomaly_window_minutes: int = 15
    rul_model_name: str = "baseline_v1"
    retrain_schedule_cron: str = "0 2 * * 0"  # Weekly Sunday 2AM


class NotificationSettings(BaseSettings):
    """Notification provider settings."""
    model_config = SettingsConfigDict(env_prefix="NOTIFY_")

    providers: List[str] = Field(default_factory=lambda: ["console"])
    smtp_host: Optional[str] = None
    smtp_port: int = 587
    smtp_user: Optional[str] = None
    smtp_password: Optional[str] = None
    smtp_from: str = "alerts@aquanexis.local"
    webhook_url: Optional[str] = None
    webhook_secret: Optional[str] = None


class SafetySettings(BaseSettings):
    """Safety system settings."""
    model_config = SettingsConfigDict(env_prefix="SAFETY_")

    enabled: bool = True
    action_timeout_seconds: int = 5
    default_leak_action: str = "close_inlet_valve"
    default_pressure_max_kpa: float = 600.0
    default_flow_min_lpm: float = 0.1
    default_pump_current_max_a: float = 2.5


class LoggingSettings(BaseSettings):
    """Logging configuration."""
    model_config = SettingsConfigDict(env_prefix="LOG_")

    level: str = "INFO"
    format: str = "json"  # json or console
    include_timestamp: bool = True
    include_level: bool = True
    include_logger: bool = True


class AppSettings(BaseSettings):
    """Main application settings."""
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # App
    env: str = Field(
        default="development",
        pattern="^(development|staging|production|test)$",
        validation_alias=AliasChoices("env", "ENV", "APP_ENV"),
    )
    demo_mode: bool = Field(
        default=False,
        validation_alias=AliasChoices("demo_mode", "DEMO_MODE"),
    )
    host: str = "0.0.0.0"
    port: int = 8000
    allowed_origins: Union[List[str], str] = Field(
        default_factory=lambda: ["http://localhost:3000", "http://localhost:5173"]
    )

    @model_validator(mode="after")
    def parse_allowed_origins(self):
        if isinstance(self.allowed_origins, str):
            self.allowed_origins = [origin.strip() for origin in self.allowed_origins.split(",")]
        return self

    # Nested settings
    database: DatabaseSettings = DatabaseSettings()
    auth: AuthSettings = AuthSettings()
    ml: MLSettings = MLSettings()
    notifications: NotificationSettings = NotificationSettings()
    safety: SafetySettings = SafetySettings()
    logging: LoggingSettings = LoggingSettings()

    @computed_field
    @property
    def is_development(self) -> bool:
        return self.env in ("development", "test")

    @computed_field
    @property
    def is_production(self) -> bool:
        return self.env == "production"


@lru_cache
def get_settings() -> AppSettings:
    """Cached settings instance."""
    return AppSettings()


# Export for convenience
settings = get_settings()