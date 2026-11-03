"""
Tests for database models and repositories.
"""

import pytest
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.device import Device, DeviceStatus
from app.models.reading import SensorReading


class TestDeviceModel:
    """Tests for Device model."""

    @pytest.mark.asyncio
    async def test_create_device(self, db_session: AsyncSession):
        """Test creating a device."""
        device = Device(
            id=uuid4(),
            serial_number="TEST-001",
            display_name="Test Device",
            model="Test Model",
            firmware_version="1.0.0",
            sensor_config={"tds": {"enabled": True}},
            calibration={"tds": {"offset": 0.0, "slope": 1.0}},
            safety_config={"leak_action": "close_inlet_valve"},
            capabilities={"tds": True, "ph": True},
            status=DeviceStatus.ACTIVE,
        )

        db_session.add(device)
        await db_session.commit()
        await db_session.refresh(device)

        assert device.id is not None
        assert device.serial_number == "TEST-001"
        assert device.display_name == "Test Device"
        assert device.model == "Test Model"
        assert device.status == DeviceStatus.ACTIVE
        assert device.created_at is not None
        assert device.updated_at is not None

    @pytest.mark.asyncio
    async def test_device_unique_serial(self, db_session: AsyncSession):
        """Test that serial numbers must be unique."""
        device1 = Device(
            id=uuid4(),
            serial_number="DUPLICATE-001",
            display_name="Device 1",
        )
        device2 = Device(
            id=uuid4(),
            serial_number="DUPLICATE-001",
            display_name="Device 2",
        )

        db_session.add(device1)
        await db_session.commit()

        db_session.add(device2)
        with pytest.raises(Exception):  # IntegrityError
            await db_session.commit()

    @pytest.mark.asyncio
    async def test_device_defaults(self, db_session: AsyncSession):
        """Test device default values."""
        device = Device(
            id=uuid4(),
            serial_number="DEFAULT-001",
        )

        db_session.add(device)
        await db_session.commit()
        await db_session.refresh(device)

        assert device.status == DeviceStatus.OFFLINE
        assert device.sensor_config == {}
        assert device.calibration == {}
        assert device.safety_config == {}
        assert device.capabilities == {}
        assert device.firmware_version is None
        assert device.display_name is None
        assert device.model is None


class TestSensorReadingModel:
    """Tests for SensorReading model."""

    @pytest.mark.asyncio
    async def test_create_reading(self, db_session: AsyncSession):
        """Test creating a sensor reading."""
        device_id = uuid4()

        # First create a device (FK constraint)
        device = Device(id=device_id, serial_number="READING-TEST-001")
        db_session.add(device)
        await db_session.commit()

        reading = SensorReading(
            device_id=device_id,
            timestamp=datetime.now(timezone.utc),
            tds=45.2,
            ec=72.1,
            ph=7.1,
            turbidity=0.3,
            temperature=23.5,
            flow=1.2,
            pressure=350.0,
            outlet_pressure=330.0,
            tank_level=78.0,
            leak_detected=False,
            pump_current=0.85,
            pump_power=200.0,
            quality_flags={"tds": {"range": "OK"}},
            overall_quality="GOOD",
        )

        db_session.add(reading)
        await db_session.commit()
        await db_session.refresh(reading)

        assert reading.id is not None
        assert reading.device_id == device_id
        assert reading.tds == 45.2
        assert reading.outlet_pressure == 330.0
        assert reading.pump_power == 200.0
        assert reading.overall_quality == "GOOD"

    @pytest.mark.asyncio
    async def test_reading_with_optional_fields(self, db_session: AsyncSession):
        """Test reading with optional sensor fields."""
        device_id = uuid4()

        device = Device(id=device_id, serial_number="OPTIONAL-TEST-001")
        db_session.add(device)
        await db_session.commit()

        reading = SensorReading(
            device_id=device_id,
            timestamp=datetime.now(timezone.utc),
            tds=50.0,
            permeate_flow=1.0,
            reject_flow=0.2,
            uv_state=True,
            vibration=0.02,
            quality_flags={},
            overall_quality="GOOD",
        )

        db_session.add(reading)
        await db_session.commit()
        await db_session.refresh(reading)

        assert reading.permeate_flow == 1.0
        assert reading.reject_flow == 0.2
        assert reading.uv_state is True
        assert reading.vibration == 0.02

    @pytest.mark.asyncio
    async def test_reading_quality_flags_jsonb(self, db_session: AsyncSession):
        """Test quality flags are stored as JSONB."""
        device_id = uuid4()

        device = Device(id=device_id, serial_number="QUALITY-TEST-001")
        db_session.add(device)
        await db_session.commit()

        flags = {
            "tds": {"range": "OK", "rate": "OK", "cross_sensor": "OK"},
            "ph": {"range": "SUSPECT", "rate": "OK", "cross_sensor": "OK"},
        }

        reading = SensorReading(
            device_id=device_id,
            timestamp=datetime.now(timezone.utc),
            tds=45.0,
            ph=8.5,
            quality_flags=flags,
            overall_quality="SUSPECT",
        )

        db_session.add(reading)
        await db_session.commit()
        await db_session.refresh(reading)

        assert reading.quality_flags == flags
        assert reading.overall_quality == "SUSPECT"
