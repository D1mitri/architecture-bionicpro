from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import date, datetime

class UserTelemetry(BaseModel):
    load_date: date
    avg_sensor_data: Optional[float]
    avg_battery_level: Optional[float]
    total_readings: Optional[int]
    data_quality_score: Optional[str]
    battery_health: Optional[str]
    etl_timestamp: datetime

class UserReport(BaseModel):
    user_id: int
    customer_name: Optional[str]
    customer_email: Optional[str]
    region: Optional[str]
    account_status: Optional[str]
    subscription_type: Optional[str]
    avg_sensor_data: Optional[float]
    avg_battery_level: Optional[float]
    total_readings: Optional[int]
    data_quality_score: Optional[str]
    battery_health: Optional[str]
    first_reading: Optional[datetime]
    last_reading: Optional[datetime]
    load_date: date
    etl_timestamp: datetime
    user_guid: Optional[str] = None
    auth_info: Optional[Dict[str, Any]] = None
    history: List[UserTelemetry] = []

class HealthCheck(BaseModel):
    status: str
    database: bool
    timestamp: datetime

class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None
    timestamp: datetime

class AuthInfo(BaseModel):
    username: str
    user_guid: str
    generated_user_id: int
    auth_method: str

class DebugResponse(BaseModel):
    message: str
    user_info: Dict[str, Any]
    calculation_details: Dict[str, Any]