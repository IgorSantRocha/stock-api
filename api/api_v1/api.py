from fastapi import APIRouter

from api.api_v1.endpoints import origin, product, movement

api_router = APIRouter()
api_router.include_router(
    origin.router, prefix="/v1/origins", tags=["Origens V1"])

api_router.include_router(
    product.router, prefix="/v1/products", tags=["Produtos V1"])

api_router.include_router(
    movement.router, prefix="/v1/movements", tags=["Movimentos V1"])
