"""
WebSocket manager for real-time telemetry and alert updates.
"""

import asyncio
import json
from datetime import datetime
from typing import Dict, List, Set
from uuid import UUID

from fastapi import WebSocket
from pydantic import BaseModel

from app.infrastructure.logging import get_logger

logger = get_logger(__name__)


class WSMessage(BaseModel):
    """Base WebSocket message."""

    type: str
    device_id: UUID
    timestamp: str
    payload: dict


class ConnectionManager:
    """Manages WebSocket connections per device."""

    def __init__(self):
        # device_id -> set of WebSocket connections
        self._connections: Dict[UUID, Set[WebSocket]] = {}
        self._device_locks: Dict[UUID, asyncio.Lock] = {}

    async def connect(self, websocket: WebSocket, device_id: UUID) -> None:
        """Register a new WebSocket connection for a device."""
        await websocket.accept()

        if device_id not in self._connections:
            self._connections[device_id] = set()
            self._device_locks[device_id] = asyncio.Lock()

        self._connections[device_id].add(websocket)
        logger.info(
            "ws_connected", device_id=str(device_id), total=len(self._connections[device_id])
        )

    def disconnect(self, websocket: WebSocket, device_id: UUID) -> None:
        """Remove a WebSocket connection."""
        if device_id in self._connections:
            self._connections[device_id].discard(websocket)
            if not self._connections[device_id]:
                del self._connections[device_id]
                if device_id in self._device_locks:
                    del self._device_locks[device_id]
        logger.info("ws_disconnected", device_id=str(device_id))

    async def broadcast(self, device_id: UUID, message: dict) -> None:
        """Broadcast a message to all connections for a device."""
        if device_id not in self._connections:
            return

        message_json = json.dumps(message)
        dead_connections = set()

        for ws in self._connections[device_id]:
            try:
                await ws.send_text(message_json)
            except Exception as e:
                logger.warning("ws_send_failed", device_id=str(device_id), error=str(e))
                dead_connections.add(ws)

        # Clean up dead connections
        for ws in dead_connections:
            self.disconnect(ws, device_id)

    async def broadcast_telemetry(self, device_id: UUID, telemetry_data: dict) -> None:
        """Broadcast telemetry update."""
        await self.broadcast(
            device_id,
            {
                "type": "telemetry",
                "device_id": str(device_id),
                "timestamp": datetime.utcnow().isoformat(),
                "data": telemetry_data,
            },
        )

    async def broadcast_alert(self, device_id: UUID, alert_data: dict, event_type: str) -> None:
        """Broadcast alert event."""
        # Map backend event types to frontend expected types
        frontend_event_type = event_type
        if event_type == "alert.created":
            frontend_event_type = "alert_created"
        elif event_type == "alert.updated":
            frontend_event_type = "alert_updated"
        elif event_type == "alert.auto_cleared":
            frontend_event_type = "alert_updated"

        await self.broadcast(
            device_id,
            {
                "type": frontend_event_type,
                "device_id": str(device_id),
                "timestamp": datetime.utcnow().isoformat(),
                "data": alert_data,
            },
        )

    async def broadcast_device_status(self, device_id: UUID, status: str, last_seen: str) -> None:
        """Broadcast device status change."""
        await self.broadcast(
            device_id,
            {
                "type": "device_status",
                "device_id": str(device_id),
                "timestamp": datetime.utcnow().isoformat(),
                "data": {
                    "status": status,
                    "last_seen": last_seen,
                },
            },
        )

    async def broadcast_sensor_health(self, device_id: UUID, sensor_health: dict) -> None:
        """Broadcast sensor health change."""
        await self.broadcast(
            device_id,
            {
                "type": "sensor_health",
                "device_id": str(device_id),
                "timestamp": datetime.utcnow().isoformat(),
                "data": sensor_health,
            },
        )

    def get_connection_count(self, device_id: UUID) -> int:
        """Get number of active connections for a device."""
        return len(self._connections.get(device_id, set()))

    def get_all_devices(self) -> List[UUID]:
        """Get list of devices with active connections."""
        return list(self._connections.keys())


# Global connection manager
ws_manager = ConnectionManager()
