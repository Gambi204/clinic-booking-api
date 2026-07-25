from datetime import date, datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query, status
from sqlalchemy.orm import Session

from app.api.errors import APIError
from app.core.clock import get_current_time
from app.core.config import settings
from app.db.dependencies import get_db
from app.schemas import (
    AvailabilitySlot,
    DoctorAvailabilityResponse,
    ErrorResponse,
)
from app.services import (
    AppointmentConflictError,
    AppointmentValidationError,
    ResourceNotFoundError,
    get_doctor_availability,
)


router = APIRouter(tags=["Doctors"])


@router.get(
    "/doctors/{doctor_id}/availability",
    response_model=DoctorAvailabilityResponse,
    status_code=status.HTTP_200_OK,
    summary="Get doctor availability",
    description=(
        "Return available 30-minute appointment slots for a doctor "
        "on a specified clinic date."
    ),
    responses={
        400: {
            "model": ErrorResponse,
            "description": "The requested date is invalid.",
        },
        404: {
            "model": ErrorResponse,
            "description": "The doctor does not exist.",
        },
        409: {
            "model": ErrorResponse,
            "description": "The doctor is inactive.",
        },
    },
)
def get_availability(
    doctor_id: Annotated[
        int,
        Path(
            gt=0,
            description="Identifier of the doctor.",
        ),
    ],
    service_date: Annotated[
        date,
        Query(
            alias="date",
            description=(
                "Clinic date for which availability is requested."
            ),
            examples=["2026-07-27"],
        ),
    ],
    database_session: Annotated[Session, Depends(get_db)],
    current_time: Annotated[datetime, Depends(get_current_time)],
) -> DoctorAvailabilityResponse:
    """Return valid unoccupied slots for the requested doctor."""

    try:
        doctor, available_starts = get_doctor_availability(
            database_session,
            doctor_id=doctor_id,
            service_date=service_date,
            now=current_time,
        )
    except ResourceNotFoundError as error:
        raise APIError(
            status_code=status.HTTP_404_NOT_FOUND,
            code=error.code,
            message=error.message,
        ) from error
    except AppointmentConflictError as error:
        raise APIError(
            status_code=status.HTTP_409_CONFLICT,
            code=error.code,
            message=error.message,
        ) from error
    except AppointmentValidationError as error:
        raise APIError(
            status_code=status.HTTP_400_BAD_REQUEST,
            code=error.code,
            message=error.message,
        ) from error

    slot_duration = timedelta(
        minutes=settings.slot_duration_minutes,
    )

    return DoctorAvailabilityResponse(
        doctor_id=doctor.id,
        doctor_name=doctor.full_name,
        date=service_date,
        timezone=settings.clinic_timezone,
        slot_duration_minutes=settings.slot_duration_minutes,
        available_slots=[
            AvailabilitySlot(
                start_at=slot_start,
                end_at=slot_start + slot_duration,
            )
            for slot_start in available_starts
        ],
    )