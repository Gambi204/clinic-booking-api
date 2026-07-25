from datetime import datetime

from pydantic import BaseModel

from app.models.appointment import AppointmentStatus


class PatientAppointmentItem(BaseModel):
    """One upcoming appointment belonging to a patient."""

    id: int

    doctor_id: int
    doctor_name: str
    doctor_specialty: str

    start_at: datetime
    end_at: datetime

    status: AppointmentStatus


class PatientAppointmentsResponse(BaseModel):
    """Upcoming appointments for one patient."""

    patient_id: int
    patient_name: str

    timezone: str
    appointments: list[PatientAppointmentItem]