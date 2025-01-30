# backend/uart_service.py

import serial
import json
import asyncio
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class UARTService:
    def __init__(self):
        self.serial = None
        self.connected = False
        
    async def connect(self, port: str = '/dev/ttyUSB0', baudrate: int = 115200) -> bool:
        """Connect to Arduino via UART"""
        try:
            self.serial = serial.Serial(port, baudrate, timeout=0)
            self.connected = True
            logger.info(f"Connected to Arduino on {port}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Arduino: {str(e)}")
            return False
    
    async def disconnect(self):
        """Disconnect from Arduino"""
        if self.serial:
            self.serial.close()
        self.connected = False
    
    async def read_data(self) -> Optional[Dict[str, Any]]:
        """Read and parse data from Arduino. Could be voltage update or station reading."""
        if not self.connected or not self.serial:
            return None
            
        try:
            if self.serial.in_waiting:
                line = self.serial.readline().decode('utf-8').strip()
                if line:
                    # Parse Arduino's JSON format
                    data = json.loads(line)
                    
                    # Check packet type based on content
                    if 'voltage' in data:
                        return {'supply_voltage': data['voltage']}
                    elif all(k in data for k in ['id', 'motor', 'switch']):
                        return {
                            'station_id': data['id'],
                            'motor_current': data['motor'],
                            'switch_current': data['switch']
                        }
        except Exception as e:
            logger.error(f"Error reading from Arduino: {str(e)}")
        
        return None
    
    async def send_state(self, enabled_stations: list[int], speed: int, master_enabled: bool) -> bool:
        """Send system state to Arduino"""
        if not self.connected or not self.serial:
            return False
            
        try:
            # Format: {"enabled":[1,2,4],"speed":6,"master":true}
            state = {
                "enabled": enabled_stations,
                "speed": speed,
                "master": master_enabled
            }
            
            command = json.dumps(state) + '\n'
            self.serial.write(command.encode('utf-8'))
            return True
        except Exception as e:
            logger.error(f"Error sending state to Arduino: {str(e)}")
            return False
    
    async def stop_all(self) -> bool:
        """Send command to stop all stations"""
        if not self.connected or not self.serial:
            return False
            
        try:
            # Simple stop command: "X"
            self.serial.write(b"X\n")
            return True
        except Exception as e:
            logger.error(f"Error sending stop command to Arduino: {str(e)}")
            return False

    async def update_settings(self, settings: dict) -> bool:
        """Send updated settings to Arduino"""
        if not self.connected or not self.serial:
            return False
            
        try:
            # Format: {"settings": {"speed": 6, "cutoff": 11.1}}
            command = {
                "settings": {
                    "speed": settings["cyclesPerMinute"],
                    "cutoff": settings["cutoffVoltage"]
                }
            }
            
            command_str = json.dumps(command) + '\n'
            self.serial.write(command_str.encode('utf-8'))
            return True
        except Exception as e:
            logger.error(f"Error sending settings to Arduino: {str(e)}")
            return False 