# backend/websocket_manager.py

from fastapi import WebSocket
from typing import List, Dict, Any
import logging

class WebSocketManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.logger = logging.getLogger(__name__)

    async def connect(self, websocket: WebSocket):
        """Accept a new WebSocket connection"""
        try:
            await websocket.accept()
            self.active_connections.append(websocket)
            self.logger.info(f"New WebSocket connection. Total connections: {len(self.active_connections)}")
        except Exception as e:
            self.logger.error(f"Failed to accept WebSocket connection: {e}")
            raise

    async def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection"""
        try:
            self.active_connections.remove(websocket)
            self.logger.info(f"WebSocket disconnected. Remaining connections: {len(self.active_connections)}")
        except ValueError:
            self.logger.warning("Attempted to remove non-existent WebSocket connection")
        except Exception as e:
            self.logger.error(f"Error during WebSocket disconnection: {e}")

    async def broadcast(self, message: Dict[str, Any]):
        """Send a message to all connected clients"""
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                self.logger.error(f"Failed to send message to WebSocket: {e}")
                disconnected.append(connection)

        # Clean up any disconnected clients
        for connection in disconnected:
            await self.disconnect(connection) 