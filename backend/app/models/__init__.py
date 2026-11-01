"""
Database models package.
Import all models here so they're registered with SQLAlchemy Base.
"""
from app.models.device import Device
from app.models.reading import SensorReading
from app.models.alert import Alert

__all__ = ["Device", "SensorReading", "Alert"]