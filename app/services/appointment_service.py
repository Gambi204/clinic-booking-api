from datetime import datetime

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session, selectinload

from app.models import (
    Appointment,
    AppointmentStatus,
    Doctor,
    Patient,
)
from app.services.exceptions import (
    AppointmentConflictError,
    ResourceNotFoundError,
)
from app.services.scheduling import (
    normalize_to_clinic_timezone,
    validate_appointment_start,
)


SCHEDULED_DOCTOR_SLOT_INDEX = (
    "uq_appointments_scheduled_doctor_start"
)


def get_integrity_constraint_name(
    error: IntegrityError,
) -> str | None:
    """Extract the PostgreSQL constraint or index name from an error."""

    diagnostics = getattr(error.orig, "diag", None)

    return getattr(diagnostics, "constraint_name", None)


def create_appointment(
    database_session: Session,
    *,
    doctor_id: int,
    patient_id: int,
    requested_start: datetime,
    now: datetime | None = None,
) -> Appointment:
    """Validate and persist a new scheduled appointment."""

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

    patient = database_session.get(Patient, patient_id)

    if patient is None:
        raise ResourceNotFoundError(
            code="PATIENT_NOT_FOUND",
            message=f"Patient {patient_id} was not found.",
        )

    normalized_start = validate_appointment_start(
        requested_start,
        doctor.working_hours,
        now=now,
    )

    existing_appointment_id = database_session.scalar(
        select(Appointment.id).where(
            Appointment.doctor_id == doctor_id,
            Appointment.start_at == normalized_start,
            Appointment.status
            == AppointmentStatus.SCHEDULED.value,
        )
    )

    if existing_appointment_id is not None:
        raise AppointmentConflictError(
            code="SLOT_UNAVAILABLE",
            message=(
                "The requested appointment slot is no longer "
                "available."
            ),
        )

    appointment = Appointment(
        doctor_id=doctor_id,
        patient_id=patient_id,
        start_at=normalized_start,
        status=AppointmentStatus.SCHEDULED.value,
    )

    database_session.add(appointment)

    try:
        database_session.commit()
    except IntegrityError as error:
        database_session.rollback()

        if (
            get_integrity_constraint_name(error)
            == SCHEDULED_DOCTOR_SLOT_INDEX
        ):
            raise AppointmentConflictError(
                code="SLOT_UNAVAILABLE",
                message=(
                    "The requested appointment slot is no longer "
                    "available."
                ),
            ) from error

        raise

    database_session.refresh(appointment)

    return appointment

def cancel_appointment(
    database_session: Session,
    *,
    appointment_id: int,
    reason: str,
    now: datetime,
) -> Appointment:
    """Cancel an appointment while preserving its history."""

    appointment = database_session.scalar(
        select(Appointment)
        .where(Appointment.id == appointment_id)
        .with_for_update()
    )

    if appointment is None:
        raise ResourceNotFoundError(
            code="APPOINTMENT_NOT_FOUND",
            message=f"Appointment {appointment_id} was not found.",
        )

    if appointment.status == AppointmentStatus.CANCELLED.value:
        raise AppointmentConflictError(
            code="APPOINTMENT_ALREADY_CANCELLED",
            message=(
                f"Appointment {appointment_id} has already been "
                "cancelled."
            ),
        )

    cancellation_time = normalize_to_clinic_timezone(
        now,
        field_name="now",
    )

    appointment.status = AppointmentStatus.CANCELLED.value
    appointment.cancellation_reason = reason
    appointment.cancelled_at = cancellation_time

    try:
        database_session.commit()
    except SQLAlchemyError:
        database_session.rollback()
        raise

    database_session.refresh(appointment)

    return appointment