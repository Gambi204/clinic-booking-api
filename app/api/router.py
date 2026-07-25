from fastapi import APIRouter

from app.api.routes.appointments import router as appointments_router
from app.api.routes.doctors import router as doctors_router


api_router = APIRouter()

api_router.include_router(appointments_router)
api_router.include_router(doctors_router)