from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List


class PackageCreate(BaseModel):
    name: str = Field(..., description="Package name", examples=["Basic Service"])
    description: str = Field(..., description="Brief description of the package")
    price: float = Field(..., description="Package price in RM", ge=0, examples=[150.00])
    estimated_duration_minutes: int = Field(..., description="Estimated service time in minutes", ge=1, examples=[60])
    services: List[str] = Field(..., description="List of services included", examples=[["Engine oil change", "Oil filter replacement", "Tyre rotation"]])
    is_active: bool = Field(True, description="Whether this package is available for booking")


class PackageUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = Field(None, ge=0)
    estimated_duration_minutes: Optional[int] = Field(None, ge=1)
    services: Optional[List[str]] = None
    is_active: Optional[bool] = None


class PackageOut(BaseModel):
    id: str
    name: str
    description: str
    price: float
    estimated_duration_minutes: int
    services: List[str]
    is_active: bool
    created_at: Optional[datetime] = None
