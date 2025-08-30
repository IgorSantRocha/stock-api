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
        movement_in: MovementPayload,
) -> Any:
    """
    Cria um novo moveiment

    1. Verifica se o item já existe, se não existir, cria o item
    2. Cria o movimento
    3. Atualiza o location e o status do item de acordo com o movimento
    4. Retorna o Item para que seja visualizada a sua posição final

    :item.status -> Recebe "IN_DEPOT", "IN_TRANSIT", "WITH_CLIENT", "WITH_CUSTOMER" (para mais detalhes, ver schemas/item_schema.py)

    """
    # verifica se o produto já existe, se existir, ignora a criação
    existing_movement = await movement.get_last_by_filters(
        db=db,
        filters={
            'sku': {'operator': '==', 'value': movement_in.sku},
            'description': {'operator': '==', 'value': movement_in.description}
        }
    )
    if existing_movement:
        logger.info("Produto já existe, ignorando criação...")
        return existing_movement

    logger.info("Criando novo movement...")
    _movement = await movement.create(db=db, obj_in=movement_in)
    return _movement
