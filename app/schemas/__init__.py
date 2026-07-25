from app.schemas.appointment import (
    AppointmentCancellationResponse,
    AppointmentCancelRequest,
    AppointmentCreate,
    AppointmentResponse,
)
from app.schemas.availability import (
    AvailabilitySlot,
    DoctorAvailabilityResponse,
)
from app.schemas.error import ErrorDetail, ErrorResponse

__all__ = [
    "AppointmentCancellationResponse",
    "AppointmentCancelRequest",
    "AppointmentCreate",
    "AppointmentResponse",
    "AvailabilitySlot",
    "DoctorAvailabilityResponse",
    "ErrorDetail",
    "ErrorResponse",
]