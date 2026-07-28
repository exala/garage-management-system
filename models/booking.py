from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from models.appointment import AppointmentOut, AppointmentStatus


class BookingRequest(BaseModel):
    # --- Customer ---
    phone: str = Field(..., description="Customer phone number (used as unique ID)", examples=["+60123456789"])
    name: str = Field(..., description="Customer full name", examples=["Ali Hassan"])

    # --- Vehicle ---
    registration_number: str = Field(..., description="Vehicle plate number", examples=["WXY 1234"])
    make: str = Field(..., description="Car manufacturer", examples=["Toyota"])
    model: str = Field(..., description="Car model", examples=["Vios"])
    year: int = Field(..., description="Manufacturing year", ge=1900, le=2100, examples=[2020])
    color: Optional[str] = Field(None, description="Car color", examples=["Silver"])

    # --- Appointment ---
    package_id: str = Field(..., description="ID of the maintenance package selected")
    scheduled_at: datetime = Field(..., description="Requested appointment date and time")
    notes: Optional[str] = Field(None, description="Any special requests or notes")


class BookingResponse(BaseModel):
    appointment: AppointmentOut

    # What happened — useful for the frontend to show the right confirmation message
    customer_created: bool = Field(..., description="True if a new customer record was created")
    vehicle_created: bool = Field(..., description="True if a new vehicle record was created")

    message: str = Field(..., description="Human-readable summary of what was done")
