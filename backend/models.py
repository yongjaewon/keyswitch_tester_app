from sqlalchemy import Boolean, Column, Integer, Float, DateTime, ForeignKey, String
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class Station(Base):
    __tablename__ = "stations"
    
    id = Column(Integer, primary_key=True)  # 1-4
    enabled = Column(Boolean, default=True)  # Managed by server, controls servo via Arduino
    currentCycles = Column(Integer, default=0)  # Counted by server
    motorCurrent = Column(Float, default=0.0)  # From Arduino, in Amps
    switchCurrent = Column(Float, default=0.0)  # From Arduino, in Amps
    motorFailures = Column(Integer, default=0)  # Calculated by server based on motorCurrent
    switchFailures = Column(Integer, default=0)  # Calculated by server based on switchCurrent
    lastUpdated = Column(DateTime, default=datetime.utcnow)  # Timestamp of last Arduino reading
    
    history = relationship("SystemHistory", back_populates="station")

class SystemState(Base):
    __tablename__ = "system_state"
    
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    supplyVoltage = Column(Float, default=13.2)  # From Arduino
    masterEnabled = Column(Boolean, default=False)  # Managed by server
    timerHours = Column(Integer, default=0)  # Managed by server
    timerMinutes = Column(Integer, default=0)  # Managed by server
    timerSeconds = Column(Integer, default=0)  # Managed by server
    timerActive = Column(Boolean, default=False)  # Managed by server

class SystemHistory(Base):
    __tablename__ = "system_history"
    
    id = Column(Integer, primary_key=True)
    station_id = Column(Integer, ForeignKey("stations.id"))
    timestamp = Column(DateTime, default=datetime.utcnow)
    cycleLimit = Column(Integer)  # System setting at time of recording
    currentCycles = Column(Integer)  # Station's cycle count
    motorFailures = Column(Integer)  # Station's motor failures
    switchFailures = Column(Integer)  # Station's switch failures
    motorCurrent = Column(Float)  # Station's motor current from Arduino
    switchCurrent = Column(Float)  # Station's switch current from Arduino
    cyclesPerMinute = Column(Integer)  # System setting at time of recording
    supplyVoltage = Column(Float)  # System voltage from Arduino
    masterEnabled = Column(Boolean)  # System state at time of recording
    
    station = relationship("Station", back_populates="history")

class SystemSettings(Base):
    __tablename__ = "system_settings"
    
    id = Column(Integer, primary_key=True)
    pin_code = Column(String(4), nullable=False)
    cyclesPerMinute = Column(Integer, default=6)  # Controls servo timing
    cutoffVoltage = Column(Float, default=11.1)  # Threshold for Arduino voltage
    motorCurrentThreshold = Column(Float, default=100.0)  # Threshold for failure detection
    switchCurrentThreshold = Column(Float, default=5.0)   # Threshold for failure detection
    cycleLimit = Column(Integer, default=100000)  # Max cycles before auto-disable
    motorFailureThreshold = Column(Integer, default=10)  # Max failures before auto-disable
    switchFailureThreshold = Column(Integer, default=10)  # Max failures before auto-disable
