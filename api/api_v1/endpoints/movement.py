from typing import Any, List
import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from crud.crud_movement import movement
from crud.crud_movement import movement
from crud.crud_item import item

from schemas.product_schema import ProductCreate, ProductUpdate, ProductInDbBase
from schemas.item_schema import ItemCreate, ItemUpdate, ItemInDbBase
from schemas.movement_schema import MovementCreate, MovementPayload, MovementInDbBase
from services.movement import MovementService

from api import deps

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/", response_model=List[MovementInDbBase])
async def read_movements(
        db: Session = Depends(deps.get_db_psql),
        skip: int = 0,
        limit: int = 100,
) -> Any:
    """
    Consulta todas as movimentos possíveis
    """
    logger.info("Consultando movements...")
    return await movement.get_multi(db=db, skip=skip, limit=limit)


@router.post("/", response_model=ItemInDbBase)
async def create_movement(
        *,
        db: Session = Depends(deps.get_db_psql),
        payload: MovementPayload,
) -> Any:
    """
    Cria um novo moveiment
    """
    service = MovementService()
    service_response = await service.create_movement(db=db, payload=payload)

    return service_response
