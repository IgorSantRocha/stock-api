from typing import Any, List, Annotated
import logging

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from crud.crud_movement import movement
from crud.crud_item import item
from schemas.item_schema import ItemCreate, ItemUpdate, ItemInDbBase, ItemPedidoInDbBase


from api import deps

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/list/{client}", response_model=List[ItemInDbBase])
async def read_items_by_client(
        client: str,
        status: str,
        sales_channels: Annotated[list[str] | None,
                                  Query(alias="sales_channels[]")] = None,
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
    filters = [
        {"field": "status", "operator": "=", "value": status},
        {"field": "product.client_name", "operator": "=", "value": client},
    ]
    if sales_channels:
        filters.append({"field": "location.sales_channel",
                       "operator": "in", "value": sales_channels})

    itens = await item.list_with_filters(
        db=db,
        filters=filters,
        order_by="created_at",
        order_desc=True,
        distinct_on_id=True,  # <--- ativa DISTINCT ON (Item.id)
    )
    return itens


@router.get("/{serial}", response_model=ItemInDbBase)
async def read_item(
        client: str,
        serial: str,
        db: Session = Depends(deps.get_db_psql)
) -> Any:
    """
    # Consulta um item por client e serial
    """
    logger.info("Consultando products por client...")
    filters = {
        'serial': {'operator': '==', 'value': serial},
        'product.client_name': {'operator': '==', 'value': client}
    }

    itens = await item.get_last_by_filters(
        db=db,
        filters=filters,
    )
    if not itens:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found (O serial informado não existe ou não pertence a este cliente)",
        )
    return itens


@router.get("/{serial}/pedido", response_model=ItemPedidoInDbBase)
async def read_item(
        client: str,
        serial: str,
        db: Session = Depends(deps.get_db_psql)
) -> Any:
    """
    # Consulta um item por client e serial e retorna o pedido do movimento
    """
    logger.info("Consultando products por client...")
    filters = {
        'serial': {'operator': '==', 'value': serial},
        'product.client_name': {'operator': '==', 'value': client}
    }

    itens = await item.get_last_by_filters(
        db=db,
        filters=filters,
    )
    if not itens:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found (O serial informado não existe ou não pertence a este cliente)",
        )

    movimento = await movement.get_last_by_filters(
        db=db,
        filters={
            'item_id': {'operator': '==', 'value': itens.id}
        }
    )
    if movimento.movement_type != 'IN':
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item sem pedido (O item não possui um movimento de entrada associado)",
        )

    itens.in_order_number = movimento.order_number

    return itens
