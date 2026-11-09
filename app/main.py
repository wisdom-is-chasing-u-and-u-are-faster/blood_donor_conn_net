"""FastAPI application entrypoint for Blood Donor Connection Network."""

import os
from fastapi import FastAPI, status
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.routers.donors import router as donors_router

app = FastAPI(
    title="Blood Donor Connection Network - Eligibility Engine",
    description="Biological Cooldown Verification and Donor Eligibility Engine (ARCH-7525)",
    version="1.0.0",
)

# Include donor eligibility routes
app.include_router(donors_router)


@app.get("/health", tags=["system"], summary="Health and readiness probe")
def health_check():
    """Returns application health and status."""
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"status": "healthy", "service": "blood_donor_conn_net"},
    )


# Mount public directory if present for static frontend serving
if os.path.exists("public"):
    if os.path.exists("public/pages"):
        app.mount("/pages", StaticFiles(directory="public/pages"), name="pages")
    app.mount("/", StaticFiles(directory="public", html=True), name="public")
