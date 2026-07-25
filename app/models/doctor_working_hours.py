from __future__ import annotations

from datetime import time
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    SmallInteger,
    Time,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.doctor import Doctor


class DoctorWorkingHours(Base):
    """A period during which a doctor accepts appointments."""

    __tablename__ = "doctor_working_hours"

    __table_args__ = (
        CheckConstraint(
            "weekday BETWEEN 0 AND 6",
            name="weekday_range",
        ),
        CheckConstraint(
            "start_time < end_time",
            name="valid_time_range",
        ),
        UniqueConstraint(
            "doctor_id",
            "weekday",
            "start_time",
            "end_time",
            name="uq_doctor_working_hours_period",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    doctor_id: Mapped[int] = mapped_column(
        ForeignKey(
            "doctors.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    weekday: Mapped[int] = mapped_column(
        SmallInteger,
        nullable=False,
    )

    start_time: Mapped[time] = mapped_column(
        Time,
        nullable=False,
    )

    end_time: Mapped[time] = mapped_column(
        Time,
        nullable=False,
    )

    doctor: Mapped["Doctor"] = relationship(
        back_populates="working_hours",
    )