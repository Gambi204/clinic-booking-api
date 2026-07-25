from fastapi import APIRouter

from app.api.routes.appointments import router as appointments_router


api_router = APIRouter()

api_router.include_router(appointments_router)