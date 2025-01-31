# backend/main.py

from fastapi import FastAPI, WebSocket, HTTPException, Depends, APIRouter, Path, Body
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import asyncio
import logging
import os
from typing import Dict, List, Optional
from datetime import datetime, timedelta, timezone
from contextlib import asynccontextmanager
from starlette.websockets import WebSocketDisconnect
from dotenv import load_dotenv

from database import get_db, init_db
from models import Station, SystemSettings, SystemState, SystemHistory
from uart_service import UARTService
from websocket_manager import WebSocketManager
from schemas import (
    StationStateUpdate,
    TimerSettings,
    SystemSettingsUpdate,
    StationResponse,
    SystemStatusResponse,
    SystemSettingsResponse,
    SuccessResponse
)

# Load environment variables
load_dotenv()

# Configure structured logging
logging.basicConfig(
    level=getattr(logging, os.getenv('LOG_LEVEL', 'INFO')),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Environment variables
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
UPDATE_FREQUENCY = float(os.getenv("UPDATE_FREQUENCY", "0.5"))
MAX_TIMER_HOURS = int(os.getenv("MAX_TIMER_HOURS", "24"))
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))
SERIAL_PORT = os.getenv("SERIAL_PORT", "/dev/ttyUSB0")
BAUD_RATE = int(os.getenv("BAUD_RATE", "115200"))

# Initialize FastAPI app
background_tasks = []

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database
    init_db()
    
    # Initialize UART service
    uart_service = UARTService()
    await uart_service.connect(port=SERIAL_PORT, baudrate=BAUD_RATE)
    
    # Initialize WebSocket manager
    websocket_manager = WebSocketManager()
    
    # Store services in app state
    app.state.uart_service = uart_service
    app.state.websocket_manager = websocket_manager
    app.state.system_state = SystemState()
    
    # Start background tasks
    background_tasks.append(asyncio.create_task(monitor_status(app)))
    
    try:
        yield
    finally:
        # Cleanup
        for task in background_tasks:
            task.cancel()
        await asyncio.gather(*background_tasks, return_exceptions=True)
        await uart_service.disconnect()

app = FastAPI(
    title="Keyswitch Tester API",
    version="1.0.0",
    description="API for controlling and monitoring the keyswitch tester system",
    lifespan=lifespan
)

# Create API router with prefix
api_router = APIRouter(prefix="/api")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# Initialize services
uart = UARTService()
ws_manager = WebSocketManager()

# Track low voltage state
voltage_monitor = {
    'low_voltage_start': None  # Timestamp when voltage first dropped below cutoff
}

@asynccontextmanager
async def get_db_context():
    """Context manager for database sessions"""
    db = next(get_db())
    try:
        yield db
    finally:
        db.close()

async def broadcast_status_update(db: Session):
    """Helper function to broadcast current system status to all clients"""
    system_state = db.query(SystemState).first()
    if not system_state:
        logger.error("System state not found when trying to broadcast status")
        raise HTTPException(status_code=500, detail="System state not found")
        
    stations = db.query(Station).all()
    
    # Format the timer end time in UTC without microseconds
    timer_end_time = None
    if system_state.timerEndTime:
        timer_end_time = system_state.timerEndTime.replace(microsecond=0).strftime('%Y-%m-%dT%H:%M:%SZ')
    
    status_update = {
        'type': 'status_update',
        'data': {
            'supplyVoltage': system_state.supplyVoltage,
            'masterEnabled': system_state.masterEnabled,
            'timerActive': system_state.timerActive,
            'timerEndTime': timer_end_time,
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
                for s in stations
            ]
        }
    }
    
    logger.debug(f"Broadcasting status update: {status_update}")
    await ws_manager.broadcast(status_update)

def calculate_end_time(hours: int, minutes: int) -> Optional[datetime]:
    """
    Calculate the UTC end time for a timer
    
    Args:
        hours: Number of hours for timer (0-MAX_TIMER_HOURS)
        minutes: Number of minutes for timer (0-59)
        
    Returns:
        datetime: UTC end time, or None if timer is being cleared
        
    Raises:
        ValueError: If hours or minutes are invalid
    """
    if hours < 0 or hours >= MAX_TIMER_HOURS:
        raise ValueError(f"Hours must be between 0 and {MAX_TIMER_HOURS}")
    if minutes < 0 or minutes >= 60:
        raise ValueError("Minutes must be between 0 and 59")
        
    if hours == 0 and minutes == 0:
        return None
        
    # Use UTC time for all calculations
    now = datetime.now(timezone.utc).replace(microsecond=0)
    return now + timedelta(hours=hours, minutes=minutes)

async def ensure_system_state(db: Session) -> SystemState:
    """
    Ensure system state exists in database
    
    Args:
        db: Database session
        
    Returns:
        SystemState: Current system state
        
    Raises:
        HTTPException: If system state cannot be created
    """
    try:
        system_state = db.query(SystemState).first()
        if not system_state:
            system_state = SystemState()
            db.add(system_state)
            db.commit()
        return system_state
    except Exception as e:
        logger.error(f"Error ensuring system state: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to ensure system state")

# Authentication middleware
async def verify_pin(pin: str, db: Session = Depends(get_db)):
    settings = db.query(SystemSettings).first()
    if pin != settings.pin_code:
        raise HTTPException(status_code=401, detail="Invalid PIN")
    return True

# Background task for status monitoring
async def monitor_status(app: FastAPI):
    """Background task for monitoring system status"""
    try:
        while True:
            try:
                # Get latest reading from Arduino (if connected)
                arduino_data = await app.state.uart_service.read_data() if app.state.uart_service.connected else None
                
                async with get_db_context() as db:
                    system_state = await ensure_system_state(db)
                    settings = db.query(SystemSettings).first()
                    if not settings:
                        logger.error("System settings not found")
                        continue
                    
                    # Check if timer has expired
                    if system_state.timerActive and system_state.timerEndTime:
                        current_time = datetime.now(timezone.utc).replace(microsecond=0)
                        timer_end_time = system_state.timerEndTime.replace(tzinfo=timezone.utc)
                        logger.info(f"Checking timer expiration - Current time: {current_time.isoformat()}, End time: {timer_end_time.isoformat()}")
                        if current_time >= timer_end_time:
                            logger.info("Timer expired, stopping system")
                            system_state.masterEnabled = False
                            system_state.timerActive = False
                            system_state.timerEndTime = None
                            db.commit()
                            
                            # Send stop command to Arduino if connected
                            if app.state.uart_service.connected:
                                await app.state.uart_service.stop_all()
                            
                            # Broadcast the updated state
                            await broadcast_status_update(db)
                            continue
                        else:
                            logger.debug(f"Timer not expired yet. Time remaining: {(timer_end_time - current_time).total_seconds()} seconds")

                    # Process Arduino data if available
                    if arduino_data:
                        # Handle supply voltage updates
                        if 'supply_voltage' in arduino_data:
                            system_state.supplyVoltage = arduino_data['supply_voltage']
                            
                            # Check voltage against cutoff
                            if system_state.masterEnabled and system_state.supplyVoltage < settings.cutoffVoltage:
                                current_time = datetime.now(timezone.utc)
                                
                                # If this is the first time voltage dropped below cutoff
                                if voltage_monitor['low_voltage_start'] is None:
                                    voltage_monitor['low_voltage_start'] = current_time
                                    logger.warning(f"Supply voltage dropped below cutoff: {system_state.supplyVoltage}V < {settings.cutoffVoltage}V")
                                
                                # If voltage has been below cutoff for more than 5 seconds
                                elif (current_time - voltage_monitor['low_voltage_start']).total_seconds() >= 5:
                                    logger.error(f"Supply voltage below cutoff for >5 seconds, stopping system")
                                    system_state.masterEnabled = False
                                    voltage_monitor['low_voltage_start'] = None  # Reset the timer
                                    
                                    # Send stop command to Arduino if connected
                                    if app.state.uart_service.connected:
                                        await app.state.uart_service.stop_all()
                            else:
                                # Reset the low voltage timer if voltage is above cutoff
                                if voltage_monitor['low_voltage_start'] is not None:
                                    logger.info(f"Supply voltage restored: {system_state.supplyVoltage}V")
                                    voltage_monitor['low_voltage_start'] = None
                            
                            db.commit()
                        
                        # Handle station current readings
                        elif all(k in arduino_data for k in ['station_id', 'motor_current', 'switch_current']):
                            station = db.query(Station).filter_by(id=arduino_data['station_id']).first()
                            if station:
                                settings = db.query(SystemSettings).first()
                                if not settings:
                                    logger.error("System settings not found")
                                    continue
                                
                                # Update current readings
                                station.motorCurrent = arduino_data['motor_current']
                                station.switchCurrent = arduino_data['switch_current']
                                station.lastUpdated = datetime.now(timezone.utc)
                                station.currentCycles += 1
                                
                                # Check for failures
                                if station.motorCurrent > settings.motorCurrentThreshold:
                                    station.motorFailures += 1
                                    logger.warning(f"Station {station.id} motor failure detected")
                                if station.switchCurrent > settings.switchCurrentThreshold:
                                    station.switchFailures += 1
                                    logger.warning(f"Station {station.id} switch failure detected")
                                
                                # Auto-disable if limits reached
                                if (station.currentCycles >= settings.cycleLimit or
                                    station.motorFailures >= settings.motorFailureThreshold or
                                    station.switchFailures >= settings.switchFailureThreshold):
                                    station.enabled = False
                                    logger.info(f"Station {station.id} auto-disabled due to limits reached")
                                
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
                    
            except asyncio.CancelledError:
                logger.info("Monitor status task cancelled")
                return  # Exit cleanly on cancellation
            except Exception as e:
                logger.error(f"Error in status monitoring: {str(e)}")
                await asyncio.sleep(1)  # Wait longer on error
            
            await asyncio.sleep(UPDATE_FREQUENCY)
    except asyncio.CancelledError:
        logger.info("Monitor status task cancelled")
        return  # Exit cleanly on cancellation

# Background task for sending state to Arduino
async def send_arduino_state():
    """Background task for sending system state to Arduino"""
    try:
        while True:
            try:
                # Skip if Arduino is not connected
                if not uart.connected:
                    await asyncio.sleep(UPDATE_FREQUENCY)
                    continue
                    
                async with get_db_context() as db:
                    system_state = db.query(SystemState).first()
                    settings = db.query(SystemSettings).first()
                    
                    if not all([system_state, settings]):
                        logger.error("Missing system state or settings")
                        await asyncio.sleep(1)
                        continue
                    
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
                    
            except asyncio.CancelledError:
                logger.info("Send Arduino state task cancelled")
                return  # Exit cleanly on cancellation
            except Exception as e:
                logger.error(f"Error sending state to Arduino: {str(e)}")
                await asyncio.sleep(1)
            
            await asyncio.sleep(UPDATE_FREQUENCY)
    except asyncio.CancelledError:
        logger.info("Send Arduino state task cancelled")
        return  # Exit cleanly on cancellation

# WebSocket endpoint - keep this at root level
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        while True:
            try:
                data = await websocket.receive_text()
                logger.info(f"Received WebSocket message: {data}")
            except WebSocketDisconnect:
                logger.info("Client disconnected normally")
                break
            except Exception as e:
                logger.error(f"Error processing WebSocket message: {str(e)}")
                break
    finally:
        await ws_manager.disconnect(websocket)

# API Routes
@api_router.post("/auth")
async def authenticate(pin: str, db: Session = Depends(get_db)):
    """Verify PIN code"""
    if await verify_pin(pin, db):
        return {"success": True}

@api_router.get("/settings", response_model=SystemSettingsResponse)
async def get_settings(db: Session = Depends(get_db)):
    """Get current system settings"""
    settings = db.query(SystemSettings).first()
    if not settings:
        raise HTTPException(status_code=500, detail="System settings not found")
    return SystemSettingsResponse(
        cutoffVoltage=settings.cutoffVoltage,
        motorCurrentThreshold=settings.motorCurrentThreshold,
        switchCurrentThreshold=settings.switchCurrentThreshold,
        cycleLimit=settings.cycleLimit,
        motorFailureThreshold=settings.motorFailureThreshold,
        switchFailureThreshold=settings.switchFailureThreshold,
        cyclesPerMinute=settings.cyclesPerMinute
    )

@api_router.post("/settings", response_model=SuccessResponse)
async def update_settings(settings: SystemSettingsUpdate, db: Session = Depends(get_db)):
    """Update system settings"""
    current_settings = db.query(SystemSettings).first()
    for key, value in settings.dict().items():
        setattr(current_settings, key, value)
    db.commit()
    
    # Update Arduino settings
    await uart.update_settings(settings.dict())
    return SuccessResponse(success=True)

@api_router.get("/status", response_model=SystemStatusResponse)
async def get_status(db: Session = Depends(get_db)):
    """Get current system status"""
    system_state = db.query(SystemState).first()
    stations = db.query(Station).all()
    
    return SystemStatusResponse(
        masterEnabled=system_state.masterEnabled if system_state else False,
        supplyVoltage=system_state.supplyVoltage if system_state else 13.2,
        timerActive=system_state.timerActive if system_state else False,
        timerEndTime=system_state.timerEndTime if system_state else None,
        stations=[
            StationResponse(
                id=station.id,
                enabled=station.enabled,
                motorFailures=station.motorFailures,
                switchFailures=station.switchFailures,
                currentCycles=station.currentCycles,
                motorCurrent=station.motorCurrent,
                switchCurrent=station.switchCurrent
            )
            for station in stations
        ]
    )

@api_router.post("/test/start", response_model=SuccessResponse)
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
    return SuccessResponse(success=True)

@api_router.post("/test/stop", response_model=SuccessResponse)
async def stop_test(db: Session = Depends(get_db)):
    """Stop the testing system"""
    try:
        system_state = db.query(SystemState).first()
        if not system_state:
            raise HTTPException(status_code=500, detail="System state not found")
            
        # Always set masterEnabled to false when stop is pressed
        system_state.masterEnabled = False
        
        # If timer was running, clear it
        if system_state.timerActive:
            system_state.timerActive = False
            system_state.timerEndTime = None
            
        db.commit()

        # Send stop command to Arduino if connected
        if uart.connected:
            await uart.stop_all()

        # Broadcast the updated state
        await broadcast_status_update(db)
        return SuccessResponse(success=True)
    except Exception as e:
        logger.error(f"Error stopping test: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to stop test")

@api_router.post("/station/{station_id}/state", response_model=SuccessResponse)
async def set_station_state(
    station_id: int = Path(..., ge=1, le=4, description="Station ID (1-4)"),
    state: StationStateUpdate = Body(...),
    db: Session = Depends(get_db)
):
    """Set station enabled/disabled state"""
    station = db.query(Station).filter_by(id=station_id).first()
    if not station:
        raise HTTPException(status_code=404, detail=f"Station {station_id} not found")
    
    system_state = db.query(SystemState).first()
    if not system_state:
        raise HTTPException(status_code=500, detail="System state not found")
    
    try:
        station.enabled = state.enabled
        db.commit()

        # Broadcast the updated state
        await broadcast_status_update(db)
        return SuccessResponse(success=True)
    except Exception as e:
        logger.error(f"Error updating station {station_id} state: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update station state")

@api_router.post("/timer", response_model=SuccessResponse)
async def set_timer(timer: TimerSettings, db: Session = Depends(get_db)):
    """Set system timer with hours and minutes. Setting both to 0 clears the timer."""
    system_state = db.query(SystemState).first()
    if not system_state:
        system_state = SystemState()
        db.add(system_state)
    
    # Calculate end time
    timer_end_time = calculate_end_time(timer.hours, timer.minutes)
    
    # If clearing timer (setting to 0), just clear timer state without affecting masterEnabled
    if timer_end_time is None:
        system_state.timerEndTime = None
        system_state.timerActive = False
    else:
        # Setting a new timer
        system_state.timerEndTime = timer_end_time
        system_state.timerActive = True
        # If setting a non-zero timer, ensure system is started
        if not system_state.masterEnabled:
            system_state.masterEnabled = True
            # Send start command to Arduino if connected
            if uart.connected:
                await uart.start_all()
    
    db.commit()

    # Broadcast the updated state
    await broadcast_status_update(db)
    
    return SuccessResponse(success=True)

# Include the API router
app.include_router(api_router)

if __name__ == "__main__":
    import uvicorn
    import signal
    
    # Configure uvicorn to handle signals properly
    config = uvicorn.Config(
        app=app,
        host=HOST,
        port=PORT,
        log_level="debug",
        loop="asyncio"
    )
    server = uvicorn.Server(config)
    server.run() 