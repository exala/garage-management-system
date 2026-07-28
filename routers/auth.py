import os
import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/auth", tags=["Auth"])


class LoginRequest(BaseModel):
    email: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    instructions: str = (
        'Copy the access_token above. Click the green "Authorize" button '
        'at the top of this page, paste it in, then click Authorize.'
    )


@router.post(
    "/login",
    response_model=LoginResponse,
    summary="Sign in and get a token for Swagger",
    description=(
        "Sign in with your Supabase admin email and password. "
        "Copy the **access_token** from the response, then click the "
        "**Authorize** button at the top of this page and paste it in."
    ),
)
async def login(body: LoginRequest):
    supabase_url = os.environ.get("SUPABASE_URL", "").rstrip("/")
    if not supabase_url:
        raise HTTPException(status_code=500, detail="SUPABASE_URL not configured")

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{supabase_url}/auth/v1/token?grant_type=password",
            json={"email": body.email, "password": body.password},
            headers={"apikey": os.environ.get("SUPABASE_SERVICE_KEY", "")},
        )

    if resp.status_code != 200:
        detail = resp.json().get("error_description") or resp.json().get("msg") or "Login failed"
        raise HTTPException(status_code=401, detail=detail)

    data = resp.json()
    return LoginResponse(access_token=data["access_token"])
