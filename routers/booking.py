from fastapi import APIRouter, HTTPException, Depends, status
from database import get_db
from models.booking import BookingRequest, BookingResponse
from models.appointment import AppointmentStatus
from supabase import Client

router = APIRouter(prefix="/book", tags=["Booking"])


@router.post(
    "/",
    response_model=BookingResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Book an appointment (smart upsert)",
    description="""
Single endpoint for the customer-facing booking flow.

**Logic:**
- If the customer (phone) **does not exist** → creates the customer and the vehicle, then books the appointment.
- If the customer **exists** but the vehicle (registration number) **does not** → creates only the vehicle, then books.
- If both **already exist** → books the appointment directly, no duplicates created.

Returns the new appointment plus two flags (`customer_created`, `vehicle_created`) so the
frontend can show the right confirmation message.
""",
)
def smart_book(payload: BookingRequest, db: Client = Depends(get_db)):
    customer_created = False
    vehicle_created = False

    # ── 1. Customer upsert ────────────────────────────────────────────────────
    existing_customer = (
        db.table("customers").select("phone").eq("phone", payload.phone).execute()
    )

    if not existing_customer.data:
        result = db.table("customers").insert(
            {"phone": payload.phone, "name": payload.name}
        ).execute()
        if not result.data:
            raise HTTPException(status_code=500, detail="Failed to create customer record")
        customer_created = True

    # ── 2. Vehicle upsert (matched by registration number + customer phone) ──
    existing_vehicle = (
        db.table("vehicles")
        .select("id")
        .eq("registration_number", payload.registration_number)
        .eq("customer_phone", payload.phone)
        .execute()
    )

    if existing_vehicle.data:
        vehicle_id = existing_vehicle.data[0]["id"]
    else:
        # Also check if the plate is registered to a *different* customer
        plate_check = (
            db.table("vehicles")
            .select("id", "customer_phone")
            .eq("registration_number", payload.registration_number)
            .execute()
        )
        if plate_check.data:
            raise HTTPException(
                status_code=409,
                detail=(
                    f"Vehicle {payload.registration_number} is already registered "
                    "under a different customer. Please contact the garage."
                ),
            )

        new_vehicle = db.table("vehicles").insert({
            "customer_phone": payload.phone,
            "registration_number": payload.registration_number,
            "make": payload.make,
            "model": payload.model,
            "year": payload.year,
            "color": payload.color,
        }).execute()
        if not new_vehicle.data:
            raise HTTPException(status_code=500, detail="Failed to create vehicle record")
        vehicle_id = new_vehicle.data[0]["id"]
        vehicle_created = True

    # ── 3. Verify package is active ──────────────────────────────────────────
    package = (
        db.table("packages")
        .select("id", "name")
        .eq("id", payload.package_id)
        .eq("is_active", True)
        .execute()
    )
    if not package.data:
        raise HTTPException(
            status_code=404,
            detail="Maintenance package not found or is no longer available",
        )

    # ── 4. Book the appointment ──────────────────────────────────────────────
    appointment_data = {
        "customer_phone": payload.phone,
        "vehicle_id": vehicle_id,
        "package_id": payload.package_id,
        "scheduled_at": payload.scheduled_at.isoformat(),
        "status": AppointmentStatus.pending,
        "notes": payload.notes,
    }
    appt_result = db.table("appointments").insert(appointment_data).execute()
    if not appt_result.data:
        raise HTTPException(status_code=500, detail="Failed to create appointment")

    # ── 5. Build response message ─────────────────────────────────────────────
    parts = []
    if customer_created:
        parts.append("new customer registered")
    if vehicle_created:
        parts.append("vehicle added")
    parts.append("appointment booked")
    message = ", ".join(p.capitalize() for p in parts) + "."

    return BookingResponse(
        appointment=appt_result.data[0],
        customer_created=customer_created,
        vehicle_created=vehicle_created,
        message=message,
    )
