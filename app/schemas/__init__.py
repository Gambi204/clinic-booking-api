from app.schemas.appointment import (
    AppointmentCreate,
    AppointmentResponse,
)
from app.schemas.availability import (
    AvailabilitySlot,
    DoctorAvailabilityResponse,
)
from app.schemas.error import ErrorDetail, ErrorResponse

__all__ = [
    "AppointmentCreate",
    "AppointmentResponse",
    "AvailabilitySlot",
    "DoctorAvailabilityResponse",
    "ErrorDetail",
    "ErrorResponse",
]