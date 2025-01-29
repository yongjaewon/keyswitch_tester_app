from sqlalchemy import Boolean, Column, Integer, Float, DateTime, ForeignKey, String
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class Station(Base):
    __tablename__ = "stations"
    
    id = Column(Integer, primary_key=True)  # 1-4
    enabled = Column(Boolean, default=True)
    motorFailures = Column(Integer, default=0)
    switchFailures = Column(Integer, default=0)
    currentCycles = Column(Integer, default=0)
    motorCurrent = Column(Float, default=0.0)  # in Amps
    switchCurrent = Column(Float, default=0.0)  # in Amps
    
    history = relationship("SystemHistory", back_populates="station")

class SystemState(Base):
    __tablename__ = "system_state"
    
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    supplyVoltage = Column(Float, default=13.2)
    masterEnabled = Column(Boolean, default=False)
    timerHours = Column(Integer, default=0)
    timerMinutes = Column(Integer, default=0)
    timerSeconds = Column(Integer, default=0)
    timerActive = Column(Boolean, default=False)

class SystemHistory(Base):
    __tablename__ = "system_history"
    
    id = Column(Integer, primary_key=True)
    station_id = Column(Integer, ForeignKey("stations.id"))
    timestamp = Column(DateTime, default=datetime.utcnow)
    cycleLimit = Column(Integer)
    currentCycles = Column(Integer)
    motorFailures = Column(Integer)
    switchFailures = Column(Integer)
    motorCurrent = Column(Float)
    switchCurrent = Column(Float)
    cyclesPerMinute = Column(Integer)
    supplyVoltage = Column(Float)
    masterEnabled = Column(Boolean)
    
    station = relationship("Station", back_populates="history")

class SystemSettings(Base):
    __tablename__ = "system_settings"
    
    id = Column(Integer, primary_key=True)
    pin_code = Column(String(4), nullable=False)
    cyclesPerMinute = Column(Integer, default=6)
    cutoffVoltage = Column(Float, default=11.1)
    motorCurrentThreshold = Column(Float, default=100.0)  # in Amps
    switchCurrentThreshold = Column(Float, default=5.0)   # in Amps
    cycleLimit = Column(Integer, default=100000)
    motorFailureThreshold = Column(Integer, default=10)
    switchFailureThreshold = Column(Integer, default=10)
