import asyncio
import json
import logging
from typing import Any, Dict, List
from fastapi import WebSocket

logger = logging.getLogger("rumah.websocket")


class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        async with self._lock:
            self.active_connections.append(websocket)
        logger.info("WebSocket connected. Total clients: %d", len(self.active_connections))

    async def disconnect(self, websocket: WebSocket):
        async with self._lock:
            if websocket in self.active_connections:
                self.active_connections.remove(websocket)
        logger.info("WebSocket disconnected. Total clients: %d", len(self.active_connections))

    async def broadcast(self, message: Dict[str, Any]):
        """Broadcast JSON payload to all connected clients."""
        payload_str = json.dumps(message)
        async with self._lock:
            disconnected = []
            for connection in self.active_connections:
                try:
                    await connection.send_text(payload_str)
                except Exception:
                    disconnected.append(connection)
            for dead in disconnected:
                if dead in self.active_connections:
                    self.active_connections.remove(dead)


ws_manager = ConnectionManager()
