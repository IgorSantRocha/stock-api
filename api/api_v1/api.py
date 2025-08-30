from fastapi import APIRouter

from api.api_v1.endpoints import origin, product

api_router = APIRouter()
api_router.include_router(
    origin.router, prefix="/origins", tags=["Origens V1"])

api_router.include_router(
    product.router, prefix="/products", tags=["Produtos V1"])
