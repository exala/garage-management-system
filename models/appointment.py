from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from enum import Enum


class AppointmentStatus(str, Enum):
    pending = "pending"
    confirmed = "confirmed"
    in_progress = "in_progress"
    completed = "completed"
    cancelled = "cancelled"


class AppointmentCreate(BaseModel):
    customer_phone: str = Field(..., description="Phone number of the customer")
    vehicle_id: str = Field(..., description="ID of the vehicle to be serviced")
    package_id: str = Field(..., description="ID of the maintenance package selected")
    scheduled_at: datetime = Field(..., description="Requested appointment date and time")
    notes: Optional[str] = Field(None, description="Any special instructions or notes from the customer")


class AppointmentUpdate(BaseModel):
    scheduled_at: Optional[datetime] = None
    status: Optional[AppointmentStatus] = None
    notes: Optional[str] = None


class AppointmentOut(BaseModel):
    id: str
    customer_phone: str
    vehicle_id: str
    package_id: str
    scheduled_at: datetime
    status: AppointmentStatus
    notes: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
