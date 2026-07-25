from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models import (
    Appointment,
    AppointmentStatus,
    Patient,
)
from app.services.exceptions import ResourceNotFoundError
from app.services.scheduling import (
    get_clinic_timezone,
    normalize_to_clinic_timezone,
)


def get_upcoming_patient_appointments(
    database_session: Session,
    *,
    patient_id: int,
    now: datetime | None = None,
) -> tuple[Patient, list[Appointment]]:
    """Return a patient's upcoming scheduled appointments."""

    clinic_timezone = get_clinic_timezone()

    current_time = (
        datetime.now(clinic_timezone)
        if now is None
        else normalize_to_clinic_timezone(
            now,
            field_name="now",
        )
    )

    patient = database_session.get(Patient, patient_id)

    if patient is None:
        raise ResourceNotFoundError(
            code="PATIENT_NOT_FOUND",
            message=f"Patient {patient_id} was not found.",
        )

    appointments = list(
        database_session.scalars(
            select(Appointment)
            .options(selectinload(Appointment.doctor))
            .where(
                Appointment.patient_id == patient_id,
                Appointment.status
                == AppointmentStatus.SCHEDULED.value,
                Appointment.start_at >= current_time,
            )
            .order_by(
                Appointment.start_at,
                Appointment.id,
            )
        ).all()
    )

    return patient, appointments