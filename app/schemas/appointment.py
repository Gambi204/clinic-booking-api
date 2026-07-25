from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

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


class AppointmentResponse(BaseModel):
    """Appointment details returned after successful creation."""

    id: int
    doctor_id: int
    patient_id: int

    start_at: datetime
    end_at: datetime

    status: AppointmentStatus
    created_at: datetime