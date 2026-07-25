from app.schemas.appointment import (
    AppointmentCancellationResponse,
    AppointmentCancelRequest,
    AppointmentCreate,
    AppointmentRescheduleRequest,
    AppointmentRescheduleResponse,
    AppointmentResponse,
)
from app.schemas.availability import (
    AvailabilitySlot,
    DoctorAvailabilityResponse,
)
from app.schemas.error import ErrorDetail, ErrorResponse
from app.schemas.patient import (
    PatientAppointmentItem,
    PatientAppointmentsResponse,
)

__all__ = [
    "AppointmentCancellationResponse",
    "AppointmentCancelRequest",
    "AppointmentCreate",
    "AppointmentRescheduleRequest",
    "AppointmentRescheduleResponse",
    "AppointmentResponse",
    "AvailabilitySlot",
    "DoctorAvailabilityResponse",
    "ErrorDetail",
    "ErrorResponse",
    "PatientAppointmentItem",
    "PatientAppointmentsResponse",
]