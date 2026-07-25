from fastapi import FastAPI

app = FastAPI(
    title="Clinic Booking API",
    description=(
        "A REST API for managing doctor availability and patient appointments."
    ),
    version="0.1.0",
)


@app.get("/", tags=["System"], summary="Display service information")
def root() -> dict[str, str]:
    """Return basic information about the API."""
    return {
        "name": "Clinic Booking API",
        "status": "running",
        "documentation": "/docs",
        "health": "/health",
    }


@app.get("/health", tags=["System"], summary="Check service health")
def health_check() -> dict[str, str]:
    """Confirm that the API process is running."""
    return {
        "status": "healthy",
        "service": "clinic-booking-api",
    }