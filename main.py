import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from routers import customers, vehicles, packages, appointments, maintenance, auth, booking


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Validate required secrets on startup."""
    required = ["SUPABASE_URL", "SUPABASE_SERVICE_KEY", "SUPABASE_JWT_SECRET"]
    missing = [k for k in required if not os.environ.get(k)]
    if missing:
        raise RuntimeError(f"Missing required environment variables: {', '.join(missing)}")
    yield


# ── Inner API app ────────────────────────────────────────────────────────────
# Mounted at /api by the root app below.
# Routes here are relative to that mount point, e.g.:
#   /customers/  →  external: /api/customers/
#   /docs        →  external: /api/docs
# Starlette automatically sets root_path="/api" so Swagger's "Try it out"
# sends requests to the correct external URLs.

api = FastAPI(
    title="Garage Maintenance API",
    description="""
## Garage Preventive Maintenance System

Manage customers, vehicles, maintenance packages, appointment bookings, and service history.

### Authentication
Endpoints marked **admin** require a Supabase JWT in the `Authorization: Bearer <token>` header.  
Sign in via Supabase Auth to obtain your `access_token`, then paste it into the **Authorize** button above.

### Data Model
- **Customer** — identified by phone number; one customer can own multiple vehicles.
- **Vehicle** — linked to a customer's phone; identified by registration plate.
- **Package** — a maintenance bundle (oil change, filter, etc.) with a fixed price.
- **Appointment** — links customer + vehicle + package to a scheduled time.
- **Maintenance Record** — the history entry created when an appointment is completed.
""",
    version="1.0.0",
    lifespan=lifespan,
)

api.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

api.include_router(auth.router)
api.include_router(booking.router)
api.include_router(customers.router)
api.include_router(vehicles.router)
api.include_router(packages.router)
api.include_router(appointments.router)
api.include_router(maintenance.router)


@api.get("/", include_in_schema=False)
def root_redirect():
    return RedirectResponse(url="/api/docs")


@api.get("/healthz", include_in_schema=False)
def healthz():
    return {"status": "ok"}


# ── Root ASGI app ────────────────────────────────────────────────────────────
# Strips the /api prefix before forwarding to the inner API app.
# Uvicorn is pointed at this `app` object.

app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)


@app.get("/", include_in_schema=False)
@app.get("/api", include_in_schema=False)
def root_redirect():
    return RedirectResponse(url="/api/docs")


app.mount("/api", api)
