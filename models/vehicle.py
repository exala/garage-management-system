from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class VehicleCreate(BaseModel):
    customer_phone: str = Field(..., description="Phone number of the vehicle owner")
    registration_number: str = Field(..., description="Vehicle registration / plate number", examples=["WXY 1234"])
    make: str = Field(..., description="Car manufacturer", examples=["Toyota"])
    model: str = Field(..., description="Car model", examples=["Vios"])
    year: int = Field(..., description="Manufacturing year", ge=1900, le=2100, examples=[2020])
    color: Optional[str] = Field(None, description="Car color", examples=["Silver"])


class VehicleUpdate(BaseModel):
    make: Optional[str] = None
    model: Optional[str] = None
    year: Optional[int] = Field(None, ge=1900, le=2100)
    color: Optional[str] = None


class VehicleOut(BaseModel):
    id: str
    customer_phone: str
    registration_number: str
    make: str
    model: str
    year: int
    color: Optional[str] = None
    created_at: Optional[datetime] = None
