from typing import Any, List
import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from crud.crud_item import item
from schemas.item_schema import ItemCreate, ItemUpdate, ItemInDbBase


from api import deps

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/{client}", response_model=List[ItemInDbBase])
async def read_products(
        client: str,
        status: str,
        db: Session = Depends(deps.get_db_psql)
) -> Any:
    """
    # Consulta os items por client e status

    ### Opções de status::
    - `IN_DEPOT` -> Item no depósito
    - `IN_TRANSIT` -> Item em trânsito
    - `WITH_CLIENT` -> Item está em posse do contratante ou um de seus representantes
    - `WITH_CUSTOMER` -> Item está em posse do cliente final, ou seja, instalado
    """
    logger.info("Consultando products por client...")

    itens = await item.list_with_filters(
        db=db,
        filters=[
            {"field": "status", "operator": "=", "value": status},
            {"field": "product.client_name", "operator": "=", "value": client},
        ],
        order_by="created_at",
        order_desc=True,
        distinct_on_id=True,  # <--- ativa DISTINCT ON (Item.id)
    )
    return itens
