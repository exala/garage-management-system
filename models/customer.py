from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class CustomerCreate(BaseModel):
    phone: str = Field(..., description="Phone number — used as the unique customer ID", examples=["+60123456789"])
    name: str = Field(..., description="Full name of the customer", examples=["Ali Hassan"])


class CustomerUpdate(BaseModel):
    name: Optional[str] = Field(None, description="Updated name")


class CustomerOut(BaseModel):
    phone: str
    name: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
