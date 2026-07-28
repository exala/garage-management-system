from fastapi import APIRouter, HTTPException, Depends, status
from database import get_db
from models.customer import CustomerCreate, CustomerUpdate, CustomerOut
from auth import verify_supabase_token
from supabase import Client
from typing import List

router = APIRouter(prefix="/customers", tags=["Customers"])


@router.post("/", response_model=CustomerOut, status_code=status.HTTP_201_CREATED, summary="Register a new customer")
def create_customer(payload: CustomerCreate, db: Client = Depends(get_db)):
    """Register a new customer using their phone number as the unique ID."""
    existing = db.table("customers").select("phone").eq("phone", payload.phone).execute()
    if existing.data:
        raise HTTPException(status_code=400, detail="A customer with this phone number already exists")

    result = db.table("customers").insert(payload.model_dump()).execute()
    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to create customer")
    return result.data[0]


@router.get("/", response_model=List[CustomerOut], summary="List all customers (admin)")
def list_customers(
    db: Client = Depends(get_db),
    _: dict = Depends(verify_supabase_token),
):
    """Retrieve all registered customers. Requires admin authentication."""
    result = db.table("customers").select("*").order("created_at", desc=True).execute()
    return result.data


@router.get("/{phone}", response_model=CustomerOut, summary="Get customer by phone number")
def get_customer(phone: str, db: Client = Depends(get_db)):
    """Look up a customer by their phone number."""
    result = db.table("customers").select("*").eq("phone", phone).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Customer not found")
    return result.data[0]


@router.patch("/{phone}", response_model=CustomerOut, summary="Update customer details")
def update_customer(phone: str, payload: CustomerUpdate, db: Client = Depends(get_db)):
    """Update a customer's information (e.g. name)."""
    existing = db.table("customers").select("phone").eq("phone", phone).execute()
    if not existing.data:
        raise HTTPException(status_code=404, detail="Customer not found")

    updates = {k: v for k, v in payload.model_dump().items() if v is not None}
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")

    result = db.table("customers").update(updates).eq("phone", phone).execute()
    return result.data[0]


@router.delete("/{phone}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a customer (admin)")
def delete_customer(
    phone: str,
    db: Client = Depends(get_db),
    _: dict = Depends(verify_supabase_token),
):
    """Delete a customer record. Requires admin authentication."""
    existing = db.table("customers").select("phone").eq("phone", phone).execute()
    if not existing.data:
        raise HTTPException(status_code=404, detail="Customer not found")

    db.table("customers").delete().eq("phone", phone).execute()
