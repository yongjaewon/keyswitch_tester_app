# backend/uart_service.py

import serial
import json
import asyncio
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class UARTService:
    def __init__(self, port: str = '/dev/ttyUSB0', baudrate: int = 115200):
        self.port = port
        self.baudrate = baudrate
        self.serial = None
        self.connected = False

    async def connect(self) -> bool:
        """Connect to the Arduino"""
        try:
            self.serial = serial.Serial(self.port, self.baudrate, timeout=1)
            self.connected = True
            logger.info(f"Connected to Arduino on {self.port}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Arduino: {e}")
            return False

    async def disconnect(self):
        """Disconnect from the Arduino"""
        if self.serial:
            self.serial.close()
            self.connected = False

    async def send_command(self, command: Dict[str, Any]) -> bool:
        """Send a command to the Arduino"""
        if not self.connected:
            return False
        
        try:
            command_str = json.dumps(command) + '\n'
            self.serial.write(command_str.encode())
            return True
        except Exception as e:
            logger.error(f"Failed to send command: {e}")
            return False

    async def read_status(self) -> Optional[Dict[str, Any]]:
        """Read status from the Arduino"""
        if not self.connected:
            return None
        
        try:
            if self.serial.in_waiting:
                line = self.serial.readline().decode().strip()
                if line:
                    return json.loads(line)
        except Exception as e:
            logger.error(f"Failed to read status: {e}")
        return None

    async def start_test(self) -> bool:
        """Start the test"""
        return await self.send_command({"command": "start"})

    async def stop_test(self) -> bool:
        """Stop the test"""
        return await self.send_command({"command": "stop"})

    async def toggle_station(self, station_id: int, enabled: bool) -> bool:
        """Toggle a station's enabled state"""
        return await self.send_command({
            "command": "toggle_station",
            "station_id": station_id,
            "enabled": enabled
        })

    async def update_settings(self, settings: Dict[str, Any]) -> bool:
        """Update system settings"""
        return await self.send_command({
            "command": "update_settings",
            "settings": settings
        }) 