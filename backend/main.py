# backend/main.py

from fastapi import FastAPI, WebSocket, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import asyncio
import logging
from typing import Dict, List
from pydantic import BaseModel

from database import get_db, init_db
from models import Station, SystemSettings, SystemState
from uart_service import UARTService
from websocket_manager import WebSocketManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(title="Keyswitch Tester")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Initialize services
uart = UARTService()
ws_manager = WebSocketManager()

# Pydantic models for request/response
class StationUpdate(BaseModel):
    id: int
    enabled: bool
    motorFailures: int
    switchFailures: int
    currentCycles: int
    motorCurrent: float
    switchCurrent: float

class SystemSettingsUpdate(BaseModel):
    cutoffVoltage: float
    motorCurrentThreshold: float
    switchCurrentThreshold: float
    cycleLimit: int
    motorFailureThreshold: int
    switchFailureThreshold: int
    cyclesPerMinute: int

class TimerSettings(BaseModel):
    hours: int
    minutes: int

# Authentication middleware
async def verify_pin(pin: str, db: Session = Depends(get_db)):
    settings = db.query(SystemSettings).first()
    if pin != settings.pin_code:
        raise HTTPException(status_code=401, detail="Invalid PIN")
    return True

# Background task for status monitoring
async def monitor_status():
    while True:
        try:
            # Get status from Arduino
            status = await uart.read_status()
            if status:
                # Update database
                db = next(get_db())
                system_state = db.query(SystemState).first()
                if not system_state:
                    system_state = SystemState()
                    db.add(system_state)
                
                system_state.supplyVoltage = status.get('supply_voltage', 13.2)
                system_state.masterEnabled = status.get('master_enabled', False)
                
                for station_data in status.get('stations', []):
                    station = db.query(Station).filter_by(id=station_data['id']).first()
                    if station:
                        station.motorCurrent = station_data.get('motor_current', 0.0)
                        station.switchCurrent = station_data.get('switch_current', 0.0)
                        station.currentCycles = station_data.get('current_cycles', 0)
                        station.motorFailures = station_data.get('motor_failures', 0)
                        station.switchFailures = station_data.get('switch_failures', 0)
                
                db.commit()
                
                # Broadcast to all connected clients
                await ws_manager.broadcast({
                    'type': 'status_update',
                    'data': {
                        'supplyVoltage': system_state.supplyVoltage,
                        'masterEnabled': system_state.masterEnabled,
                        'stations': [
                            {
                                'id': station.id,
                                'enabled': station.enabled,
                                'motorFailures': station.motorFailures,
                                'switchFailures': station.switchFailures,
                                'currentCycles': station.currentCycles,
                                'motorCurrent': station.motorCurrent,
                                'switchCurrent': station.switchCurrent
                            }
                            for station in db.query(Station).all()
                        ]
                    }
                })
            await asyncio.sleep(0.5)  # Wait 500ms before next check
        except Exception as e:
            logger.error(f"Error in status monitoring: {e}")
            await asyncio.sleep(1)  # Wait longer on error

# Startup event
@app.on_event("startup")
async def startup_event():
    # Initialize database
    init_db()
    # Connect to Arduino
    if not await uart.connect():
        logger.error("Failed to connect to Arduino!")
    # Start background monitoring
    asyncio.create_task(monitor_status())

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    await uart.disconnect()

# WebSocket endpoint
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
    except:
        await ws_manager.disconnect(websocket)

# API Routes
@app.post("/auth")
async def authenticate(pin: str, db: Session = Depends(get_db)):
    """Verify PIN code"""
    if await verify_pin(pin, db):
        return {"success": True}

@app.get("/settings")
async def get_settings(db: Session = Depends(get_db)):
    """Get current system settings"""
    settings = db.query(SystemSettings).first()
    return {
        "cutoffVoltage": settings.cutoffVoltage,
        "motorCurrentThreshold": settings.motorCurrentThreshold,
        "switchCurrentThreshold": settings.switchCurrentThreshold,
        "cycleLimit": settings.cycleLimit,
        "motorFailureThreshold": settings.motorFailureThreshold,
        "switchFailureThreshold": settings.switchFailureThreshold,
        "cyclesPerMinute": settings.cyclesPerMinute
    }

@app.post("/settings")
async def update_settings(settings: SystemSettingsUpdate, db: Session = Depends(get_db)):
    """Update system settings"""
    current_settings = db.query(SystemSettings).first()
    for key, value in settings.dict().items():
        setattr(current_settings, key, value)
    db.commit()
    
    # Update Arduino settings
    await uart.update_settings(settings.dict())
    return {"success": True}

@app.get("/status")
async def get_status(db: Session = Depends(get_db)):
    """Get current system status"""
    system_state = db.query(SystemState).first()
    stations = db.query(Station).all()
    
    return {
        "masterEnabled": system_state.masterEnabled if system_state else False,
        "supplyVoltage": system_state.supplyVoltage if system_state else 13.2,
        "timerActive": system_state.timerActive if system_state else False,
        "timerHours": system_state.timerHours if system_state else 0,
        "timerMinutes": system_state.timerMinutes if system_state else 0,
        "timerSeconds": system_state.timerSeconds if system_state else 0,
        "stations": [
            {
                "id": station.id,
                "enabled": station.enabled,
                "motorFailures": station.motorFailures,
                "switchFailures": station.switchFailures,
                "currentCycles": station.currentCycles,
                "motorCurrent": station.motorCurrent,
                "switchCurrent": station.switchCurrent
            }
            for station in stations
        ]
    }

@app.post("/test/start")
async def start_test(db: Session = Depends(get_db)):
    """Start the testing system"""
    success = await uart.start_test()
    if success:
        system_state = db.query(SystemState).first()
        if not system_state:
            system_state = SystemState()
            db.add(system_state)
        system_state.masterEnabled = True
        db.commit()
    return {"success": success}

@app.post("/test/stop")
async def stop_test(db: Session = Depends(get_db)):
    """Stop the testing system"""
    success = await uart.stop_test()
    if success:
        system_state = db.query(SystemState).first()
        if system_state:
            system_state.masterEnabled = False
            system_state.timerActive = False
            system_state.timerHours = 0
            system_state.timerMinutes = 0
            system_state.timerSeconds = 0
            db.commit()
    return {"success": success}

@app.post("/station/{station_id}/toggle")
async def toggle_station(station_id: int, db: Session = Depends(get_db)):
    """Toggle station enabled state"""
    station = db.query(Station).filter_by(id=station_id).first()
    if not station:
        raise HTTPException(status_code=404, detail="Station not found")
    
    new_state = not station.enabled
    success = await uart.toggle_station(station_id, new_state)
    
    if success:
        station.enabled = new_state
        db.commit()
    
    return {"success": success}

@app.post("/timer")
async def set_timer(timer: TimerSettings, db: Session = Depends(get_db)):
    """Set system timer"""
    system_state = db.query(SystemState).first()
    if not system_state:
        system_state = SystemState()
        db.add(system_state)
    
    system_state.timerHours = timer.hours
    system_state.timerMinutes = timer.minutes
    system_state.timerSeconds = 0
    system_state.timerActive = timer.hours > 0 or timer.minutes > 0
    
    db.commit()
    return {"success": True}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 