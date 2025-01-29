# backend/database.py

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base
from typing import Generator
import os
from sqlalchemy.pool import StaticPool
import logging
from pathlib import Path

from models import Base, Station, SystemSettings, SystemState

# Configure logging
logger = logging.getLogger(__name__)

# Get the backend directory path
BACKEND_DIR = Path(__file__).parent.absolute()
DB_PATH = BACKEND_DIR / "keyswitch_tester.db"

# Create SQLite database engine
SQLALCHEMY_DATABASE_URL = f"sqlite:///{DB_PATH}"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """Dependency to get DB session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Initialize the database with required initial data"""
    try:
        # Create all tables
        Base.metadata.create_all(bind=engine)
        
        # Get a DB session
        db = SessionLocal()
        
        # Check if we need to initialize (look for SystemSettings)
        if db.query(SystemSettings).first() is None:
            logger.info("Initializing database with default values...")
            
            # Create default system settings
            default_settings = SystemSettings(
                pin_code="1234",  # Default PIN
                cyclesPerMinute=6,
                cutoffVoltage=11.1,
                motorCurrentThreshold=100.0,
                switchCurrentThreshold=5.0,
                cycleLimit=100000,
                motorFailureThreshold=10,
                switchFailureThreshold=10
            )
            db.add(default_settings)
            
            # Create initial system state
            initial_state = SystemState(
                supplyVoltage=13.2,
                masterEnabled=False,
                timerActive=False,
                timerHours=0,
                timerMinutes=0,
                timerSeconds=0
            )
            db.add(initial_state)
            
            # Create the four stations
            for station_id in range(1, 5):
                station = Station(
                    id=station_id,
                    enabled=True,
                    motorFailures=0,
                    switchFailures=0,
                    currentCycles=0,
                    motorCurrent=0.0,
                    switchCurrent=0.0
                )
                db.add(station)
            
            # Commit all changes
            db.commit()
            logger.info("Database initialized successfully!")
        else:
            logger.info("Database already initialized, skipping...")
            
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise
    finally:
        db.close()

def reset_db():
    """Reset the database to initial state (for testing/development)"""
    try:
        # Drop all tables
        Base.metadata.drop_all(bind=engine)
        # Reinitialize
        init_db()
        logger.info("Database reset successfully!")
    except Exception as e:
        logger.error(f"Error resetting database: {e}")
        raise 