from fastapi import APIRouter, HTTPException, Depends, status
from database import get_db
from models.vehicle import VehicleCreate, VehicleUpdate, VehicleOut
from supabase import Client
from typing import List

router = APIRouter(prefix="/vehicles", tags=["Vehicles"])


@router.post("/", response_model=VehicleOut, status_code=status.HTTP_201_CREATED, summary="Register a vehicle")
def register_vehicle(payload: VehicleCreate, db: Client = Depends(get_db)):
    """Register a new vehicle under a customer's phone number. One phone can have multiple vehicles."""
    # Verify customer exists
    customer = db.table("customers").select("phone").eq("phone", payload.customer_phone).execute()
    if not customer.data:
        raise HTTPException(status_code=404, detail="Customer with this phone number not found")

    # Check for duplicate registration number
    existing = db.table("vehicles").select("id").eq("registration_number", payload.registration_number).execute()
    if existing.data:
        raise HTTPException(status_code=400, detail="A vehicle with this registration number is already registered")

    result = db.table("vehicles").insert(payload.model_dump()).execute()
    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to register vehicle")
    return result.data[0]


@router.get("/customer/{phone}", response_model=List[VehicleOut], summary="Get all vehicles for a customer")
def get_vehicles_by_customer(phone: str, db: Client = Depends(get_db)):
    """List all vehicles registered under a specific phone number."""
    result = db.table("vehicles").select("*").eq("customer_phone", phone).execute()
    return result.data


@router.get("/{vehicle_id}", response_model=VehicleOut, summary="Get a specific vehicle")
def get_vehicle(vehicle_id: str, db: Client = Depends(get_db)):
    """Fetch a vehicle's details by its ID."""
    result = db.table("vehicles").select("*").eq("id", vehicle_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    return result.data[0]


@router.get("/registration/{reg_number}", response_model=VehicleOut, summary="Look up vehicle by registration")
def get_vehicle_by_registration(reg_number: str, db: Client = Depends(get_db)):
    """Look up a vehicle using its registration plate number."""
    result = db.table("vehicles").select("*").eq("registration_number", reg_number).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    return result.data[0]


@router.patch("/{vehicle_id}", response_model=VehicleOut, summary="Update vehicle details")
def update_vehicle(vehicle_id: str, payload: VehicleUpdate, db: Client = Depends(get_db)):
    """Update vehicle information (make, model, year, color)."""
    existing = db.table("vehicles").select("id").eq("id", vehicle_id).execute()
    if not existing.data:
        raise HTTPException(status_code=404, detail="Vehicle not found")

    updates = {k: v for k, v in payload.model_dump().items() if v is not None}
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")

    result = db.table("vehicles").update(updates).eq("id", vehicle_id).execute()
    return result.data[0]


@router.delete("/{vehicle_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Remove a vehicle")
def delete_vehicle(vehicle_id: str, db: Client = Depends(get_db)):
    """Remove a vehicle from the system."""
    existing = db.table("vehicles").select("id").eq("id", vehicle_id).execute()
    if not existing.data:
        raise HTTPException(status_code=404, detail="Vehicle not found")

    db.table("vehicles").delete().eq("id", vehicle_id).execute()
