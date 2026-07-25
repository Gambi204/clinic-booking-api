from datetime import datetime

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
)

from app.models.appointment import AppointmentStatus


class AppointmentCreate(BaseModel):
    """Information required to book an appointment."""

    doctor_id: int = Field(
        gt=0,
        description="Identifier of the doctor being booked.",
        examples=[1],
    )

    patient_id: int = Field(
        gt=0,
        description="Identifier of the patient making the booking.",
        examples=[1],
    )

    start_at: datetime = Field(
        description=(
            "Timezone-aware appointment start time in ISO 8601 format."
        ),
        examples=["2026-07-28T09:00:00+03:00"],
    )

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "doctor_id": 1,
                "patient_id": 1,
                "start_at": "2026-07-28T09:00:00+03:00",
            }
        },
    )


class AppointmentCancelRequest(BaseModel):
    """Information required to cancel an appointment."""

    reason: str = Field(
        min_length=3,
        max_length=500,
        description="Reason the appointment is being cancelled.",
        examples=["Patient is no longer available."],
    )

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "reason": "Patient is no longer available.",
            }
        },
    )

    @field_validator("reason")
    @classmethod
    def normalize_reason(cls, value: str) -> str:
        """Trim the reason and reject whitespace-only values."""

        normalized_reason = value.strip()

        if len(normalized_reason) < 3:
            raise ValueError(
                "Cancellation reason must contain at least "
                "3 non-whitespace characters."
            )

        return normalized_reason

class AppointmentRescheduleRequest(BaseModel):
    """Information required to move an appointment to a new slot."""

    new_start_at: datetime = Field(
        description=(
            "Timezone-aware new appointment start time in "
            "ISO 8601 format."
        ),
        examples=["2026-07-27T10:00:00+03:00"],
    )

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "new_start_at": "2026-07-27T10:00:00+03:00",
            }
        },
    )


class AppointmentRescheduleResponse(BaseModel):
    """Appointment details returned after successful rescheduling."""

    id: int
    doctor_id: int
    patient_id: int

    previous_start_at: datetime
    start_at: datetime
    end_at: datetime

    status: AppointmentStatus
    updated_at: datetime
    
class AppointmentResponse(BaseModel):
    """Appointment details returned after successful creation."""

    id: int
    doctor_id: int
    patient_id: int

    start_at: datetime
    end_at: datetime

    status: AppointmentStatus
    created_at: datetime


class AppointmentCancellationResponse(BaseModel):
    """Appointment details returned after cancellation."""

    id: int
    doctor_id: int
    patient_id: int

    start_at: datetime
    end_at: datetime

    status: AppointmentStatus
    cancellation_reason: str
    cancelled_at: datetime
    updated_at: datetime