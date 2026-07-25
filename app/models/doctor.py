from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, String, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.appointment import Appointment
    from app.models.doctor_working_hours import DoctorWorkingHours


class Doctor(Base):
    """A doctor whose schedule can be booked by patients."""

    __tablename__ = "doctors"

    id: Mapped[int] = mapped_column(primary_key=True)

    full_name: Mapped[str] = mapped_column(
        String(120),
        nullable=False,
    )

    specialty: Mapped[str] = mapped_column(
        String(120),
        nullable=False,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default=text("true"),
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    working_hours: Mapped[list["DoctorWorkingHours"]] = relationship(
        back_populates="doctor",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    appointments: Mapped[list["Appointment"]] = relationship(
        back_populates="doctor",
    )