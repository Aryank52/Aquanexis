"""
Test configuration and fixtures.
"""
import asyncio
import os
import sys
from collections.abc import AsyncGenerator
from typing import Any
from uuid import uuid4

# Set test environment variables BEFORE any other imports
os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("DB_HOST", "localhost")
os.environ.setdefault("DB_PORT", "5432")
os.environ.setdefault("DB_USER", "aquanexis")
os.environ.setdefault("DB_PASSWORD", "aquanexis")
os.environ.setdefault("DB_NAME", "aquanexis_test")
os.environ.setdefault("DEVICE_JWT_SECRET", "test-secret-minimum-32-characters-long-for-testing")
os.environ.setdefault("API_KEY_SALT", "test-salt")
os.environ.setdefault("LOG_FORMAT", "console")
os.environ.setdefault("LOG_LEVEL", "DEBUG")

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

# Now import settings after env vars are set
from app.infrastructure.config import settings
from app.infrastructure.database import Base, db_manager, get_db
from app.main import app
from app.models.device import Device, DeviceStatus


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def test_engine():
    """Create test database engine."""
    engine = create_async_engine(
        str(settings.database.url),
        poolclass=NullPool,
        echo=False,
    )

    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Cleanup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create a new database session for each test."""
    async_session = async_sessionmaker(
        bind=test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )

    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


@pytest_asyncio.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create test client with database override."""
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        yield client

    app.dependency_overrides.clear()


@pytest.fixture
def test_device() -> "Device":
    """Create a test device instance."""
    from app.models.device import Device, DeviceStatus
    return Device(
        id=uuid4(),
        serial_number="TEST-001",
        display_name="Test Device",
        model="Test Model",
        firmware_version="1.0.0",
        sensor_config={},
        calibration={},
        safety_config={},
        capabilities={},
        status=DeviceStatus.ACTIVE,
    )


@pytest.fixture
def device_jwt_token(test_device) -> str:
    """Create a valid JWT token for test device."""
    from app.infrastructure.security import create_device_token
    return create_device_token(test_device.id)


@pytest.fixture
def auth_headers(device_jwt_token: str) -> dict[str, str]:
    """Authorization headers with device JWT."""
    return {"Authorization": f"Bearer {device_jwt_token}"}