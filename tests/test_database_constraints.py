from datetime import datetime, time, timezone

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import (
    Appointment,
    AppointmentStatus,
    Doctor,
    DoctorWorkingHours,
    Patient,
)


def create_doctor(database_session: Session, name: str) -> Doctor:
    doctor = Doctor(
        full_name=name,
        specialty="General Practice",
        is_active=True,
    )
    database_session.add(doctor)
    database_session.flush()

    return doctor


def create_patient(
    database_session: Session,
    email: str,
) -> Patient:
    patient = Patient(
        full_name="Test Patient",
        email=email,
        phone_number="+254700999999",
    )
    database_session.add(patient)
    database_session.flush()

    return patient


def test_database_rejects_double_booking_for_scheduled_appointments(
    database_session: Session,
) -> None:
    doctor = create_doctor(database_session, "Dr. Constraint Test")
    first_patient = create_patient(
        database_session,
        "first.patient@example.com",
    )
    second_patient = create_patient(
        database_session,
        "second.patient@example.com",
    )

    appointment_time = datetime(
        2026,
        8,
        3,
        9,
        0,
        tzinfo=timezone.utc,
    )

    database_session.add(
        Appointment(
            doctor_id=doctor.id,
            patient_id=first_patient.id,
            start_at=appointment_time,
            status=AppointmentStatus.SCHEDULED.value,
        )
    )
    database_session.flush()

    database_session.add(
        Appointment(
            doctor_id=doctor.id,
            patient_id=second_patient.id,
            start_at=appointment_time,
            status=AppointmentStatus.SCHEDULED.value,
        )
    )

    with pytest.raises(IntegrityError):
        database_session.flush()

    database_session.rollback()


def test_cancelled_appointment_does_not_block_slot(
    database_session: Session,
) -> None:
    doctor = create_doctor(database_session, "Dr. Cancellation Test")
    first_patient = create_patient(
        database_session,
        "cancelled.patient@example.com",
    )
    second_patient = create_patient(
        database_session,
        "replacement.patient@example.com",
    )

    appointment_time = datetime(
        2026,
        8,
        4,
        10,
        0,
        tzinfo=timezone.utc,
    )

    database_session.add_all(
        [
            Appointment(
                doctor_id=doctor.id,
                patient_id=first_patient.id,
                start_at=appointment_time,
                status=AppointmentStatus.CANCELLED.value,
                cancellation_reason="Patient became unavailable.",
            ),
            Appointment(
                doctor_id=doctor.id,
                patient_id=second_patient.id,
                start_at=appointment_time,
                status=AppointmentStatus.SCHEDULED.value,
            ),
        ]
    )

    database_session.flush()


def test_database_rejects_invalid_weekday(
    database_session: Session,
) -> None:
    doctor = create_doctor(database_session, "Dr. Weekday Test")

    database_session.add(
        DoctorWorkingHours(
            doctor_id=doctor.id,
            weekday=7,
            start_time=time(8, 0),
            end_time=time(16, 0),
        )
    )

    with pytest.raises(IntegrityError):
        database_session.flush()

    database_session.rollback()


def test_database_rejects_invalid_working_time_range(
    database_session: Session,
) -> None:
    doctor = create_doctor(database_session, "Dr. Time Range Test")

    database_session.add(
        DoctorWorkingHours(
            doctor_id=doctor.id,
            weekday=0,
            start_time=time(17, 0),
            end_time=time(8, 0),
        )
    )

    with pytest.raises(IntegrityError):
        database_session.flush()

    database_session.rollback()


def test_database_rejects_duplicate_patient_email(
    database_session: Session,
) -> None:
    create_patient(
        database_session,
        "duplicate.patient@example.com",
    )

    database_session.add(
        Patient(
            full_name="Another Test Patient",
            email="duplicate.patient@example.com",
            phone_number="+254700888888",
        )
    )

    with pytest.raises(IntegrityError):
        database_session.flush()

    database_session.rollback()