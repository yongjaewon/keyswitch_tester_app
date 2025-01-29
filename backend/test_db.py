import logging
from database import SessionLocal, init_db, reset_db
from models import Station, SystemSettings, SystemState

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_database():
    """Test database initialization and verify data"""
    try:
        # Reset database to ensure clean state
        reset_db()
        
        # Get a database session
        db = SessionLocal()
        
        # Test SystemSettings
        settings = db.query(SystemSettings).first()
        assert settings is not None, "SystemSettings not created"
        assert settings.pin_code == "1234", "Incorrect default PIN"
        assert settings.cyclesPerMinute == 6, "Incorrect default cycles per minute"
        assert settings.cutoffVoltage == 11.1, "Incorrect default cutoff voltage"
        assert settings.cycleLimit == 100000, "Incorrect default cycle limit"
        assert settings.motorCurrentThreshold == 100.0, "Incorrect default motor current threshold"
        assert settings.switchCurrentThreshold == 5.0, "Incorrect default switch current threshold"
        logger.info("✓ SystemSettings verified")
        
        # Test SystemState
        state = db.query(SystemState).first()
        assert state is not None, "SystemState not created"
        assert state.masterEnabled is False, "Incorrect default master enabled state"
        assert state.supplyVoltage == 13.2, "Incorrect default supply voltage"
        logger.info("✓ SystemState verified")
        
        # Test Stations
        stations = db.query(Station).all()
        assert len(stations) == 4, "Incorrect number of stations"
        
        for station in stations:
            assert 1 <= station.id <= 4, f"Invalid station ID: {station.id}"
            assert station.enabled is True, f"Station {station.id} should be enabled by default"
            assert station.motorFailures == 0, f"Station {station.id} should have 0 motor failures"
            assert station.switchFailures == 0, f"Station {station.id} should have 0 switch failures"
            assert station.currentCycles == 0, f"Station {station.id} should have 0 current cycles"
            assert station.motorCurrent == 0.0, f"Station {station.id} should have 0.0 motor current"
            assert station.switchCurrent == 0.0, f"Station {station.id} should have 0.0 switch current"
        logger.info("✓ Stations verified")
        
        logger.info("All database tests passed successfully!")
        
    except AssertionError as e:
        logger.error(f"Test failed: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during testing: {str(e)}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    test_database() 