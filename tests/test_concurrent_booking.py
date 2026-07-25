from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, time
from threading import Barrier
from zoneinfo import ZoneInfo

from sqlalchemy import func, select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from app.models import (
    Appointment,
    AppointmentStatus,
    Doctor,
    DoctorWorkingHours,
    Patient,
)
from app.services import (
    AppointmentConflictError,
    create_appointment,
)


NAIROBI = ZoneInfo("Africa/Nairobi")

FIXED_NOW = datetime(
    2026,
    7,
    27,
    8,
    0,
    tzinfo=NAIROBI,
)

BOOKING_START = datetime(
    2026,
    7,
    27,
    9,
    0,
    tzinfo=NAIROBI,
)


def test_simultaneous_bookings_create_only_one_appointment(
    committed_database_session: Session,
    postgres_test_engine: Engine,
    monkeypatch,
) -> None:
    """
    Verify PostgreSQL prevents two simultaneous bookings of one slot.

    Both threads are paused immediately before commit. This ensures
    both requests have already checked the slot and found it free,
    forcing the database uniqueness protection to resolve the race.
    """

    doctor = Doctor(
        full_name="Dr. Concurrent Booking Test",
        specialty="General Practice",
        is_active=True,
    )

    first_patient = Patient(
        full_name="First Concurrent Patient",
        email="first.concurrent@example.com",
        phone_number="+254700666661",
    )

    second_patient = Patient(
        full_name="Second Concurrent Patient",
        email="second.concurrent@example.com",
        phone_number="+254700666662",
    )

    committed_database_session.add_all(
        [
            doctor,
            first_patient,
            second_patient,
        ]
    )
    committed_database_session.flush()

    committed_database_session.add(
        DoctorWorkingHours(
            doctor_id=doctor.id,
            weekday=0,
            start_time=time(8, 0),
            end_time=time(17, 0),
        )
    )

    committed_database_session.commit()

    doctor_id = doctor.id
    patient_ids = [
        first_patient.id,
        second_patient.id,
    ]

    commit_barrier = Barrier(
        parties=2,
        timeout=10,
    )

    original_commit = Session.commit

    def synchronized_commit(session: Session) -> None:
        """
        Pause new appointment transactions before the real commit.

        Setup commits are completed before this monkeypatch is applied,
        so only the two worker appointment commits reach the barrier.
        """

        contains_new_appointment = any(
            isinstance(instance, Appointment)
            for instance in session.new
        )

        if contains_new_appointment:
            commit_barrier.wait()

        original_commit(session)

    monkeypatch.setattr(
        Session,
        "commit",
        synchronized_commit,
    )

    def attempt_booking(
        patient_id: int,
    ) -> tuple[str, int | str]:
        """
        Attempt one booking with an independent database session.

        Each worker must own its session because SQLAlchemy sessions
        cannot safely be shared between threads.
        """

        with Session(
            bind=postgres_test_engine,
            expire_on_commit=False,
        ) as worker_session:
            try:
                appointment = create_appointment(
                    worker_session,
                    doctor_id=doctor_id,
                    patient_id=patient_id,
                    requested_start=BOOKING_START,
                    now=FIXED_NOW,
                )

                return (
                    "created",
                    appointment.id,
                )
            except AppointmentConflictError as error:
                return (
                    "conflict",
                    error.code,
                )

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [
            executor.submit(
                attempt_booking,
                patient_id,
            )
            for patient_id in patient_ids
        ]

        results = [
            future.result(timeout=15)
            for future in futures
        ]

    created_results = [
        result
        for result in results
        if result[0] == "created"
    ]

    conflict_results = [
        result
        for result in results
        if result[0] == "conflict"
    ]

    assert len(created_results) == 1
    assert len(conflict_results) == 1

    assert conflict_results[0][1] == "SLOT_UNAVAILABLE"

    with Session(bind=postgres_test_engine) as verification_session:
        scheduled_count = verification_session.scalar(
            select(func.count())
            .select_from(Appointment)
            .where(
                Appointment.doctor_id == doctor_id,
                Appointment.start_at == BOOKING_START,
                Appointment.status
                == AppointmentStatus.SCHEDULED.value,
            )
        )

        winning_patient_id = verification_session.scalar(
            select(Appointment.patient_id).where(
                Appointment.doctor_id == doctor_id,
                Appointment.start_at == BOOKING_START,
                Appointment.status
                == AppointmentStatus.SCHEDULED.value,
            )
        )

    assert scheduled_count == 1
    assert winning_patient_id in patient_ids