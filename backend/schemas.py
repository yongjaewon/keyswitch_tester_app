from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator

# Request Models
class StationStateUpdate(BaseModel):
    """Request model for updating station state"""
    enabled: bool = Field(..., description="Whether the station is enabled")

    class Config:
        json_schema_extra = {
            "example": {
                "enabled": True
            }
        }

class TimerSettings(BaseModel):
    """Request model for setting timer"""
    hours: int = Field(..., ge=0, lt=24, description="Timer hours (0-23)")
    minutes: int = Field(..., ge=0, lt=60, description="Timer minutes (0-59)")

    class Config:
        json_schema_extra = {
            "example": {
                "hours": 1,
                "minutes": 30
            }
        }

class SystemSettingsUpdate(BaseModel):
    """Request model for updating system settings"""
    cutoffVoltage: float = Field(..., ge=10.0, le=15.0, description="Cutoff voltage threshold (10-15V)")
    motorCurrentThreshold: float = Field(..., ge=0.1, le=200.0, description="Motor current threshold (0.1-200A)")
    switchCurrentThreshold: float = Field(..., ge=0.1, le=50.0, description="Switch current threshold (0.1-50A)")
    cycleLimit: int = Field(..., ge=1, le=1000000, description="Maximum cycle limit (1-1,000,000)")
    motorFailureThreshold: int = Field(..., ge=1, le=1000, description="Motor failure threshold (1-1,000)")
    switchFailureThreshold: int = Field(..., ge=1, le=1000, description="Switch failure threshold (1-1,000)")
    cyclesPerMinute: int = Field(..., ge=1, le=12, description="Cycles per minute (1-12)")

    class Config:
        json_schema_extra = {
            "example": {
                "cutoffVoltage": 12.0,
                "motorCurrentThreshold": 0.5,
                "switchCurrentThreshold": 0.3,
                "cycleLimit": 100000,
                "motorFailureThreshold": 10,
                "switchFailureThreshold": 10,
                "cyclesPerMinute": 6
            }
        }

    @field_validator('cutoffVoltage')
    @classmethod
    def validate_voltage(cls, v: float) -> float:
        if not 10.0 <= v <= 15.0:
            raise ValueError("Cutoff voltage must be between 10.0V and 15.0V")
        return round(v, 2)

    @field_validator('motorCurrentThreshold', 'switchCurrentThreshold')
    @classmethod
    def validate_current(cls, v: float, info) -> float:
        if info.field_name == 'motorCurrentThreshold' and not 0.1 <= v <= 200:
            raise ValueError("Motor current threshold must be between 0.1A and 200A")
        if info.field_name == 'switchCurrentThreshold' and not 0.1 <= v <= 50:
            raise ValueError("Switch current threshold must be between 0.1A and 50A")
        return round(v, 3)

# Response Models
class StationResponse(BaseModel):
    """Response model for station status"""
    id: int = Field(..., ge=1, le=4, description="Station ID (1-4)")
    enabled: bool = Field(..., description="Whether the station is enabled")
    motorFailures: int = Field(..., ge=0, description="Number of motor failures")
    switchFailures: int = Field(..., ge=0, description="Number of switch failures")
    currentCycles: int = Field(..., ge=0, description="Current cycle count")
    motorCurrent: float = Field(..., ge=0, description="Current motor current reading (A)")
    switchCurrent: float = Field(..., ge=0, description="Current switch current reading (A)")

    class Config:
        json_schema_extra = {
            "example": {
                "id": 1,
                "enabled": True,
                "motorFailures": 0,
                "switchFailures": 0,
                "currentCycles": 100,
                "motorCurrent": 0.5,
                "switchCurrent": 0.3
            }
        }

class SystemStatusResponse(BaseModel):
    """Response model for system status"""
    masterEnabled: bool = Field(..., description="Master enable state")
    supplyVoltage: float = Field(..., ge=0, description="Current supply voltage (V)")
    timerActive: bool = Field(..., description="Whether timer is active")
    timerEndTime: Optional[datetime] = Field(None, description="Timer end time in UTC")
    stations: List[StationResponse] = Field(..., description="List of station states")

    class Config:
        json_schema_extra = {
            "example": {
                "masterEnabled": True,
                "supplyVoltage": 13.2,
                "timerActive": True,
                "timerEndTime": "2024-03-21T15:30:00Z",
                "stations": [
                    {
                        "id": 1,
                        "enabled": True,
                        "motorFailures": 0,
                        "switchFailures": 0,
                        "currentCycles": 100,
                        "motorCurrent": 0.5,
                        "switchCurrent": 0.3
                    }
                ]
            }
        }

class SystemSettingsResponse(BaseModel):
    """Response model for system settings"""
    cutoffVoltage: float = Field(..., ge=10.0, le=15.0, description="Cutoff voltage threshold (V)")
    motorCurrentThreshold: float = Field(..., ge=0.1, le=200, description="Motor current threshold (A)")
    switchCurrentThreshold: float = Field(..., ge=0.1, le=50, description="Switch current threshold (A)")
    cycleLimit: int = Field(..., ge=1, le=1000000, description="Maximum cycle limit")
    motorFailureThreshold: int = Field(..., ge=1, le=1000, description="Motor failure threshold")
    switchFailureThreshold: int = Field(..., ge=1, le=1000, description="Switch failure threshold")
    cyclesPerMinute: int = Field(..., ge=1, le=12, description="Cycles per minute (1-12)")

    class Config:
        json_schema_extra = {
            "example": {
                "cutoffVoltage": 12.0,
                "motorCurrentThreshold": 0.5,
                "switchCurrentThreshold": 0.3,
                "cycleLimit": 100000,
                "motorFailureThreshold": 10,
                "switchFailureThreshold": 10,
                "cyclesPerMinute": 6
            }
        }

class SuccessResponse(BaseModel):
    """Generic success response"""
    success: bool = Field(..., description="Whether the operation was successful")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True
            }
        } 