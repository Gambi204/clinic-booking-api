from datetime import date, datetime, time, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models import Appointment, AppointmentStatus, Doctor
from app.services.exceptions import (
    AppointmentConflictError,
    AppointmentValidationError,
    ResourceNotFoundError,
)
from app.services.scheduling import (
    get_available_slot_starts,
    get_clinic_timezone,
    normalize_to_clinic_timezone,
)


def get_doctor_availability(
    database_session: Session,
    *,
    doctor_id: int,
    service_date: date,
    now: datetime | None = None,
) -> tuple[Doctor, list[datetime]]:
    """Return available appointment starts for a doctor and date."""

    clinic_timezone = get_clinic_timezone()

    current_time = (
        datetime.now(clinic_timezone)
        if now is None
        else normalize_to_clinic_timezone(
            now,
            field_name="now",
        )
    )

    if service_date < current_time.date():
        raise AppointmentValidationError(
            code="AVAILABILITY_DATE_IN_PAST",
            message="Availability cannot be requested for a past date.",
        )

    doctor = database_session.scalar(
        select(Doctor)
        .options(selectinload(Doctor.working_hours))
        .where(Doctor.id == doctor_id)
    )

    if doctor is None:
        raise ResourceNotFoundError(
            code="DOCTOR_NOT_FOUND",
            message=f"Doctor {doctor_id} was not found.",
        )

    if not doctor.is_active:
        raise AppointmentConflictError(
            code="DOCTOR_INACTIVE",
            message=(
                f"Doctor {doctor_id} is not currently accepting "
                "appointments."
            ),
        )

    day_start = datetime.combine(
        service_date,
        time.min,
        tzinfo=clinic_timezone,
    )

    day_end = day_start + timedelta(days=1)

    booked_starts = database_session.scalars(
        select(Appointment.start_at)
        .where(
            Appointment.doctor_id == doctor_id,
            Appointment.status
            == AppointmentStatus.SCHEDULED.value,
            Appointment.start_at >= day_start,
            Appointment.start_at < day_end,
        )
        .order_by(Appointment.start_at)
    ).all()

    available_slots = get_available_slot_starts(
        service_date,
        doctor.working_hours,
        booked_starts,
        now=current_time,
    )

    return doctor, available_slots