from typing import Any, List
import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from crud.crud_movement import movement
from crud.crud_movement import movement
from crud.crud_item import item

from schemas.product_schema import ProductCreate, ProductUpdate, ProductInDbBase
from schemas.item_schema import ItemCreate, ItemUpdate, ItemInDbBase
from schemas.movement_schema import MovementPayloadListItem, MovementPayload, MovementInDbBase
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
# Cria um novo movement

### Detalhes
- Para casos **Cielo**, o `product_id` pode ser igual a `0`
- Nesse caso:
    - Será feita a consulta síncrona para localizar o produto
    - Caso não dê certo, retorna um erro pedindo que seja enviado `product_id`

> **Nota:** Use sempre `product_id` quando disponível.
"""

    service = MovementService()
    service_response = await service.create_movement(db=db, payload=payload)

    return service_response


@router.post("/move-list-items", response_model=List[ItemInDbBase])
async def create_movement(
        *,
        db: Session = Depends(deps.get_db_psql),
        payload: MovementPayloadListItem,
) -> Any:
    """
# Cria um novo movement

### Detalhes
- Para casos **Cielo**, o `product_id` pode ser igual a `0`
- Nesse caso:
    - Será feita a consulta síncrona para localizar o produto
    - Caso não dê certo, retorna um erro pedindo que seja enviado `product_id`

> **Nota:** Use sempre `product_id` quando disponível.
"""

    service = MovementService()
    items = []
    for item in payload.item:
        payload_item = MovementPayload(
            item=item,
            client_name=payload.client_name,
            movement_type=payload.movement_type,
            from_location_id=payload.from_location_id,
            to_location_id=payload.to_location_id,
            order_origin_id=payload.order_origin_id,
            order_number=payload.order_number,
            volume_number=payload.volume_number,
            kit_number=payload.kit_number,
            created_by=payload.created_by,
            extra_info=payload.extra_info if payload.extra_info else None,
        )

        service_response = await service.create_movement(db=db, payload=payload_item)
        items.append(service_response)

    return items
