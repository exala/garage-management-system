from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class MaintenanceRecordCreate(BaseModel):
    appointment_id: str = Field(..., description="ID of the completed appointment")
    technician_notes: Optional[str] = Field(None, description="Notes from the technician after service")
    cost_actual: Optional[float] = Field(None, description="Actual final cost charged (if different from package price)", ge=0)
    completed_at: datetime = Field(..., description="Date and time the service was completed")


class MaintenanceRecordOut(BaseModel):
    id: str
    appointment_id: str
    customer_phone: str
    vehicle_id: str
    package_id: str
    technician_notes: Optional[str] = None
    cost_actual: Optional[float] = None
    completed_at: datetime
    created_at: Optional[datetime] = None
