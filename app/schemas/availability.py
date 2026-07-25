from datetime import date, datetime

from pydantic import BaseModel, Field


class AvailabilitySlot(BaseModel):
    """One available 30-minute appointment period."""

    start_at: datetime = Field(
        description="Beginning of the available appointment slot.",
    )

    end_at: datetime = Field(
        description="End of the available appointment slot.",
    )


class DoctorAvailabilityResponse(BaseModel):
    """Available appointment slots for one doctor and date."""

    doctor_id: int
    doctor_name: str
    date: date
    timezone: str
    slot_duration_minutes: int
    available_slots: list[AvailabilitySlot]