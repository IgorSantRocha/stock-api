from fastapi import APIRouter

from api.api_v1.endpoints import origin

api_router = APIRouter()
api_router.include_router(
    origin.router, prefix="/origins", tags=["Origens V1"])
