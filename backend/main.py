# backend/main.py

from fastapi import FastAPI, WebSocket, HTTPException, Depends, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import asyncio
import logging
from typing import Dict, List
from pydantic import BaseModel
from datetime import datetime

from database import get_db, init_db
from models import Station, SystemSettings, SystemState, SystemHistory
from uart_service import UARTService
from websocket_manager import WebSocketManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(title="Keyswitch Tester")

# Create API router with prefix
api_router = APIRouter(prefix="/api")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Frontend dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
uart = UARTService()
ws_manager = WebSocketManager()

async def broadcast_status_update(db: Session):
    """Helper function to broadcast current system status to all clients"""
    system_state = db.query(SystemState).first()
    if not system_state:
        logger.error("System state not found when trying to broadcast status")
        return
        
    status_update = {
        'type': 'status_update',
        'data': {
            'supplyVoltage': system_state.supplyVoltage,
            'masterEnabled': system_state.masterEnabled,
            'stations': [
                {
                    'id': s.id,
                    'enabled': s.enabled,
                    'motorFailures': s.motorFailures,
                    'switchFailures': s.switchFailures,
                    'currentCycles': s.currentCycles,
                    'motorCurrent': s.motorCurrent,
                    'switchCurrent': s.switchCurrent
                }
                for s in db.query(Station).all()
            ]
        }
    }
    logger.info(f"Broadcasting status update: {status_update}")
    await ws_manager.broadcast(status_update)

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

class StationStateUpdate(BaseModel):
    enabled: bool

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
            # Get latest reading from Arduino (could be voltage update or station reading)
            arduino_data = await uart.read_data()
            if not arduino_data:
                await asyncio.sleep(0.1)  # Short sleep if no data
                continue

            db = next(get_db())
            try:
                # Ensure system state exists
                system_state = db.query(SystemState).first()
                if not system_state:
                    system_state = SystemState()
                    db.add(system_state)
                    db.commit()
                
                # Handle supply voltage updates
                if 'supply_voltage' in arduino_data:
                    system_state.supplyVoltage = arduino_data['supply_voltage']
                    db.commit()
                
                # Handle station current readings
                elif all(k in arduino_data for k in ['station_id', 'motor_current', 'switch_current']):
                    station = db.query(Station).filter_by(id=arduino_data['station_id']).first()
                    if station:
                        settings = db.query(SystemSettings).first()
                        
                        # Update current readings
                        station.motorCurrent = arduino_data['motor_current']
                        station.switchCurrent = arduino_data['switch_current']
                        station.lastUpdated = datetime.utcnow()
                        
                        station.currentCycles += 1
                        
                        # Check for failures
                        if station.motorCurrent > settings.motorCurrentThreshold:
                            station.motorFailures += 1
                        if station.switchCurrent > settings.switchCurrentThreshold:
                            station.switchFailures += 1
                        
                        # Auto-disable if limits reached
                        if (station.currentCycles >= settings.cycleLimit or
                            station.motorFailures >= settings.motorFailureThreshold or
                            station.switchFailures >= settings.switchFailureThreshold):
                            station.enabled = False
                        
                        db.commit()
                        
                        # Record history
                        history = SystemHistory(
                            station_id=station.id,
                            currentCycles=station.currentCycles,
                            motorFailures=station.motorFailures,
                            switchFailures=station.switchFailures,
                            motorCurrent=station.motorCurrent,
                            switchCurrent=station.switchCurrent,
                            supplyVoltage=system_state.supplyVoltage,
                            masterEnabled=system_state.masterEnabled,
                            cycleLimit=settings.cycleLimit,
                            cyclesPerMinute=settings.cyclesPerMinute
                        )
                        db.add(history)
                        db.commit()
                
                # Broadcast updates to all connected clients
                await broadcast_status_update(db)
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Error in status monitoring: {e}")
            await asyncio.sleep(1)  # Wait longer on error

# Background task for sending state to Arduino
async def send_arduino_state():
    """Periodically send system state to Arduino"""
    while True:
        try:
            db = next(get_db())
            try:
                system_state = db.query(SystemState).first()
                settings = db.query(SystemSettings).first()
                if system_state and settings:
                    # Get list of enabled station IDs
                    enabled_stations = [
                        station.id 
                        for station in db.query(Station).filter_by(enabled=True).all()
                    ]
                    
                    # Send current state to Arduino
                    await uart.send_state(
                        enabled_stations=enabled_stations,
                        speed=settings.cyclesPerMinute,
                        master_enabled=system_state.masterEnabled
                    )
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Error sending state to Arduino: {str(e)}")
        
        await asyncio.sleep(0.5)  # Send state every 500ms

# Startup event
@app.on_event("startup")
async def startup_event():
    # Initialize database
    init_db()
    # Connect to Arduino
    if not await uart.connect():
        logger.error("Failed to connect to Arduino!")
    # Start background tasks
    asyncio.create_task(monitor_status())
    asyncio.create_task(send_arduino_state())
    
    logger.info("Application startup complete")

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    await uart.disconnect()

# WebSocket endpoint - keep this at root level
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            logger.info(f"Received WebSocket message: {data}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        await ws_manager.disconnect(websocket)

# API Routes
@api_router.post("/auth")
async def authenticate(pin: str, db: Session = Depends(get_db)):
    """Verify PIN code"""
    if await verify_pin(pin, db):
        return {"success": True}

@api_router.get("/settings")
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

@api_router.post("/settings")
async def update_settings(settings: SystemSettingsUpdate, db: Session = Depends(get_db)):
    """Update system settings"""
    current_settings = db.query(SystemSettings).first()
    for key, value in settings.dict().items():
        setattr(current_settings, key, value)
    db.commit()
    
    # Update Arduino settings
    await uart.update_settings(settings.dict())
    return {"success": True}

@api_router.get("/status")
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

@api_router.post("/test/start")
async def start_test(db: Session = Depends(get_db)):
    """Start the testing system"""
    system_state = db.query(SystemState).first()
    if not system_state:
        system_state = SystemState()
        db.add(system_state)
    
    system_state.masterEnabled = True
    db.commit()

    # Broadcast the updated state
    await broadcast_status_update(db)
    return {"success": True}

@api_router.post("/test/stop")
async def stop_test(db: Session = Depends(get_db)):
    """Stop the testing system"""
    # Send stop command to Arduino
    # success = await uart.stop_all()
    success = True
    if success:
        system_state = db.query(SystemState).first()
        if system_state:
            system_state.masterEnabled = False
            system_state.timerActive = False
            system_state.timerHours = 0
            system_state.timerMinutes = 0
            system_state.timerSeconds = 0
            db.commit()

            # Broadcast the updated state
            await broadcast_status_update(db)

    return {"success": success}

@api_router.post("/station/{station_id}/state")
async def set_station_state(
    station_id: int, 
    state: StationStateUpdate,
    db: Session = Depends(get_db)
):
    """Set station enabled/disabled state"""
    station = db.query(Station).filter_by(id=station_id).first()
    if not station:
        raise HTTPException(status_code=404, detail="Station not found")
    
    system_state = db.query(SystemState).first()
    if not system_state:
        raise HTTPException(status_code=500, detail="System state not found")
    
    station.enabled = state.enabled
    db.commit()

    # Broadcast the updated state
    await broadcast_status_update(db)
    return {"success": True}

@api_router.post("/timer")
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

# Include the API router
app.include_router(api_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 