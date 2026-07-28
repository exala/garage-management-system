from fastapi import APIRouter, HTTPException, Depends, status, Query
from database import get_db
from models.appointment import AppointmentCreate, AppointmentUpdate, AppointmentOut, AppointmentStatus
from auth import verify_supabase_token
from supabase import Client
from typing import List, Optional
from datetime import datetime

router = APIRouter(prefix="/appointments", tags=["Appointments"])


@router.post("/", response_model=AppointmentOut, status_code=status.HTTP_201_CREATED, summary="Book an appointment")
def book_appointment(payload: AppointmentCreate, db: Client = Depends(get_db)):
    """
    Book a maintenance appointment.
    - Customer must already be registered (phone must exist).
    - Vehicle must belong to the customer.
    - Package must be active.
    """
    # Verify customer
    customer = db.table("customers").select("phone").eq("phone", payload.customer_phone).execute()
    if not customer.data:
        raise HTTPException(status_code=404, detail="Customer not found. Please register first.")

    # Verify vehicle belongs to customer
    vehicle = db.table("vehicles").select("id").eq("id", payload.vehicle_id).eq("customer_phone", payload.customer_phone).execute()
    if not vehicle.data:
        raise HTTPException(status_code=404, detail="Vehicle not found or does not belong to this customer")

    # Verify package is active
    package = db.table("packages").select("id").eq("id", payload.package_id).eq("is_active", True).execute()
    if not package.data:
        raise HTTPException(status_code=404, detail="Maintenance package not found or is no longer available")

    data = payload.model_dump()
    data["status"] = AppointmentStatus.pending
    data["scheduled_at"] = data["scheduled_at"].isoformat()

    result = db.table("appointments").insert(data).execute()
    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to create appointment")
    return result.data[0]


@router.get("/", response_model=List[AppointmentOut], summary="List all appointments (admin)")
def list_appointments(
    status_filter: Optional[AppointmentStatus] = Query(None, alias="status", description="Filter by appointment status"),
    db: Client = Depends(get_db),
    _: dict = Depends(verify_supabase_token),
):
    """List all appointments, optionally filtered by status. Requires admin authentication."""
    query = db.table("appointments").select("*")
    if status_filter:
        query = query.eq("status", status_filter.value)
    result = query.order("scheduled_at", desc=False).execute()
    return result.data


@router.get("/customer/{phone}", response_model=List[AppointmentOut], summary="Get appointments for a customer")
def get_customer_appointments(phone: str, db: Client = Depends(get_db)):
    """Retrieve all appointments for a customer by their phone number."""
    result = (
        db.table("appointments")
        .select("*")
        .eq("customer_phone", phone)
        .order("scheduled_at", desc=True)
        .execute()
    )
    return result.data


@router.get("/{appointment_id}", response_model=AppointmentOut, summary="Get appointment details")
def get_appointment(appointment_id: str, db: Client = Depends(get_db)):
    """Fetch details of a specific appointment."""
    result = db.table("appointments").select("*").eq("id", appointment_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Appointment not found")
    return result.data[0]


@router.patch("/{appointment_id}", response_model=AppointmentOut, summary="Update appointment (admin)")
def update_appointment(
    appointment_id: str,
    payload: AppointmentUpdate,
    db: Client = Depends(get_db),
    _: dict = Depends(verify_supabase_token),
):
    """Update appointment details such as scheduled time or status. Requires admin authentication."""
    existing = db.table("appointments").select("id").eq("id", appointment_id).execute()
    if not existing.data:
        raise HTTPException(status_code=404, detail="Appointment not found")

    updates = {k: v for k, v in payload.model_dump().items() if v is not None}
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")

    if "scheduled_at" in updates and isinstance(updates["scheduled_at"], datetime):
        updates["scheduled_at"] = updates["scheduled_at"].isoformat()
    if "status" in updates and isinstance(updates["status"], AppointmentStatus):
        updates["status"] = updates["status"].value

    result = db.table("appointments").update(updates).eq("id", appointment_id).execute()
    return result.data[0]


@router.delete("/{appointment_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Cancel/delete an appointment")
def cancel_appointment(
    appointment_id: str,
    db: Client = Depends(get_db),
    _: dict = Depends(verify_supabase_token),
):
    """Cancel and remove an appointment. Requires admin authentication."""
    existing = db.table("appointments").select("id").eq("id", appointment_id).execute()
    if not existing.data:
        raise HTTPException(status_code=404, detail="Appointment not found")

    db.table("appointments").delete().eq("id", appointment_id).execute()
