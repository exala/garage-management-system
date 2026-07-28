from fastapi import APIRouter, HTTPException, Depends, status
from database import get_db
from models.package import PackageCreate, PackageUpdate, PackageOut
from auth import verify_supabase_token
from supabase import Client
from typing import List

router = APIRouter(prefix="/packages", tags=["Maintenance Packages"])


@router.get("/", response_model=List[PackageOut], summary="List available maintenance packages")
def list_packages(db: Client = Depends(get_db)):
    """List all active maintenance packages available for customers to select."""
    result = db.table("packages").select("*").eq("is_active", True).order("price").execute()
    return result.data


@router.get("/all", response_model=List[PackageOut], summary="List all packages including inactive (admin)")
def list_all_packages(
    db: Client = Depends(get_db),
    _: dict = Depends(verify_supabase_token),
):
    """List all packages including inactive ones. Requires admin authentication."""
    result = db.table("packages").select("*").order("price").execute()
    return result.data


@router.post("/", response_model=PackageOut, status_code=status.HTTP_201_CREATED, summary="Create a new package (admin)")
def create_package(
    payload: PackageCreate,
    db: Client = Depends(get_db),
    _: dict = Depends(verify_supabase_token),
):
    """Create a new maintenance package. Requires admin authentication."""
    result = db.table("packages").insert(payload.model_dump()).execute()
    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to create package")
    return result.data[0]


@router.get("/{package_id}", response_model=PackageOut, summary="Get package details")
def get_package(package_id: str, db: Client = Depends(get_db)):
    """Get details of a specific maintenance package."""
    result = db.table("packages").select("*").eq("id", package_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Package not found")
    return result.data[0]


@router.patch("/{package_id}", response_model=PackageOut, summary="Update a package (admin)")
def update_package(
    package_id: str,
    payload: PackageUpdate,
    db: Client = Depends(get_db),
    _: dict = Depends(verify_supabase_token),
):
    """Update a maintenance package's details. Requires admin authentication."""
    existing = db.table("packages").select("id").eq("id", package_id).execute()
    if not existing.data:
        raise HTTPException(status_code=404, detail="Package not found")

    updates = {k: v for k, v in payload.model_dump().items() if v is not None}
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")

    result = db.table("packages").update(updates).eq("id", package_id).execute()
    return result.data[0]


@router.delete("/{package_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a package (admin)")
def delete_package(
    package_id: str,
    db: Client = Depends(get_db),
    _: dict = Depends(verify_supabase_token),
):
    """Delete a maintenance package. Requires admin authentication."""
    existing = db.table("packages").select("id").eq("id", package_id).execute()
    if not existing.data:
        raise HTTPException(status_code=404, detail="Package not found")

    db.table("packages").delete().eq("id", package_id).execute()
