from fastapi import APIRouter, HTTPException, Depends, status
from database import get_db
from models.maintenance import MaintenanceRecordCreate, MaintenanceRecordOut
from models.appointment import AppointmentStatus
from auth import verify_supabase_token
from supabase import Client
from typing import List
from datetime import datetime

router = APIRouter(prefix="/maintenance", tags=["Maintenance History"])


@router.post("/", response_model=MaintenanceRecordOut, status_code=status.HTTP_201_CREATED, summary="Log a completed service (admin)")
def log_maintenance(
    payload: MaintenanceRecordCreate,
    db: Client = Depends(get_db),
    _: dict = Depends(verify_supabase_token),
):
    """
    Record a completed maintenance service.
    - Automatically marks the linked appointment as 'completed'.
    - Copies customer_phone, vehicle_id, and package_id from the appointment.
    Requires admin authentication.
    """
    # Fetch the appointment
    appt = db.table("appointments").select("*").eq("id", payload.appointment_id).execute()
    if not appt.data:
        raise HTTPException(status_code=404, detail="Appointment not found")

    appointment = appt.data[0]

    # Mark appointment as completed
    db.table("appointments").update({"status": AppointmentStatus.completed.value}).eq("id", payload.appointment_id).execute()

    record_data = {
        "appointment_id": payload.appointment_id,
        "customer_phone": appointment["customer_phone"],
        "vehicle_id": appointment["vehicle_id"],
        "package_id": appointment["package_id"],
        "technician_notes": payload.technician_notes,
        "cost_actual": payload.cost_actual,
        "completed_at": payload.completed_at.isoformat(),
    }

    result = db.table("maintenance_records").insert(record_data).execute()
    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to log maintenance record")
    return result.data[0]


@router.get("/customer/{phone}", response_model=List[MaintenanceRecordOut], summary="Get service history for a customer")
def get_customer_history(phone: str, db: Client = Depends(get_db)):
    """Retrieve the full maintenance history for a customer across all their vehicles."""
    result = (
        db.table("maintenance_records")
        .select("*")
        .eq("customer_phone", phone)
        .order("completed_at", desc=True)
        .execute()
    )
    return result.data


@router.get("/vehicle/{vehicle_id}", response_model=List[MaintenanceRecordOut], summary="Get service history for a vehicle")
def get_vehicle_history(vehicle_id: str, db: Client = Depends(get_db)):
    """Retrieve the maintenance history for a specific vehicle."""
    result = (
        db.table("maintenance_records")
        .select("*")
        .eq("vehicle_id", vehicle_id)
        .order("completed_at", desc=True)
        .execute()
    )
    return result.data


@router.get("/", response_model=List[MaintenanceRecordOut], summary="List all maintenance records (admin)")
def list_all_records(
    db: Client = Depends(get_db),
    _: dict = Depends(verify_supabase_token),
):
    """List all maintenance records across all customers. Requires admin authentication."""
    result = db.table("maintenance_records").select("*").order("completed_at", desc=True).execute()
    return result.data


@router.get("/{record_id}", response_model=MaintenanceRecordOut, summary="Get a specific maintenance record")
def get_record(record_id: str, db: Client = Depends(get_db)):
    """Fetch details of a single maintenance record."""
    result = db.table("maintenance_records").select("*").eq("id", record_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Maintenance record not found")
    return result.data[0]
