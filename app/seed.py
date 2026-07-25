from __future__ import annotations

from datetime import time
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models import Doctor, DoctorWorkingHours, Patient


DOCTOR_DATA: list[dict[str, Any]] = [
    {
        "full_name": "Dr. Amina Hassan",
        "specialty": "General Practice",
        "working_hours": [
            *[(weekday, "08:00", "16:00") for weekday in range(0, 5)],
        ],
    },
    {
        "full_name": "Dr. Brian Otieno",
        "specialty": "Paediatrics",
        "working_hours": [
            *[(weekday, "09:00", "17:00") for weekday in range(0, 5)],
        ],
    },
    {
        "full_name": "Dr. Carol Wanjiku",
        "specialty": "Dermatology",
        "working_hours": [
            *[
                (weekday, start_time, end_time)
                for weekday in range(0, 4)
                for start_time, end_time in (
                    ("08:30", "12:00"),
                    ("13:00", "15:30"),
                )
            ],
        ],
    },
    {
        "full_name": "Dr. David Mwangi",
        "specialty": "Orthopaedics",
        "working_hours": [
            *[(weekday, "10:00", "18:00") for weekday in range(1, 6)],
        ],
    },
    {
        "full_name": "Dr. Esther Njeri",
        "specialty": "Family Medicine",
        "working_hours": [
            *[(weekday, "07:30", "14:30") for weekday in range(0, 5)],
        ],
    },
]


PATIENT_DATA: list[dict[str, str]] = [
    {
        "full_name": "Grace Wambui",
        "email": "grace.wambui@example.com",
        "phone_number": "+254700000001",
    },
    {
        "full_name": "Peter Kamau",
        "email": "peter.kamau@example.com",
        "phone_number": "+254700000002",
    },
    {
        "full_name": "Aisha Noor",
        "email": "aisha.noor@example.com",
        "phone_number": "+254700000003",
    },
]


def parse_time(value: str) -> time:
    """Convert an HH:MM seed value into a Python time object."""

    return time.fromisoformat(value)


def seed_doctors(database_session: Session) -> tuple[int, int]:
    """Insert missing doctors and working-hour periods."""

    doctors_created = 0
    periods_created = 0

    for doctor_data in DOCTOR_DATA:
        doctor = database_session.scalar(
            select(Doctor).where(
                Doctor.full_name == doctor_data["full_name"],
            )
        )

        if doctor is None:
            doctor = Doctor(
                full_name=doctor_data["full_name"],
                specialty=doctor_data["specialty"],
                is_active=True,
            )
            database_session.add(doctor)
            database_session.flush()
            doctors_created += 1
        else:
            doctor.specialty = doctor_data["specialty"]
            doctor.is_active = True

        existing_periods = {
            (
                working_period.weekday,
                working_period.start_time,
                working_period.end_time,
            )
            for working_period in doctor.working_hours
        }

        for weekday, start_value, end_value in doctor_data["working_hours"]:
            period_key = (
                weekday,
                parse_time(start_value),
                parse_time(end_value),
            )

            if period_key in existing_periods:
                continue

            doctor.working_hours.append(
                DoctorWorkingHours(
                    weekday=weekday,
                    start_time=period_key[1],
                    end_time=period_key[2],
                )
            )
            existing_periods.add(period_key)
            periods_created += 1

    return doctors_created, periods_created


def seed_patients(database_session: Session) -> int:
    """Insert missing sample patients and update matching records."""

    patients_created = 0

    for patient_data in PATIENT_DATA:
        patient = database_session.scalar(
            select(Patient).where(
                Patient.email == patient_data["email"],
            )
        )

        if patient is None:
            database_session.add(
                Patient(
                    full_name=patient_data["full_name"],
                    email=patient_data["email"],
                    phone_number=patient_data["phone_number"],
                )
            )
            patients_created += 1
            continue

        patient.full_name = patient_data["full_name"]
        patient.phone_number = patient_data["phone_number"]

    return patients_created


def seed_database() -> None:
    """Seed the development database and report what was created."""

    with SessionLocal() as database_session:
        try:
            doctors_created, periods_created = seed_doctors(database_session)
            patients_created = seed_patients(database_session)

            database_session.commit()
        except Exception:
            database_session.rollback()
            raise

    print("Database seeding completed.")
    print(f"Doctors created: {doctors_created}")
    print(f"Working-hour periods created: {periods_created}")
    print(f"Patients created: {patients_created}")


if __name__ == "__main__":
    seed_database()