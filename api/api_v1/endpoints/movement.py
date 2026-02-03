from typing import Any, List
import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from crud.crud_movement import movement
from crud.crud_origin import origin
from crud.crud_item import item as item_crud
from crud.crud_romaneio import romaneio_crud

from schemas.product_schema import ProductCreate, ProductUpdate, ProductInDbBase
from schemas.item_schema import ItemCreate, ItemUpdate, ItemInDbBase
from schemas.movement_schema import MovementPayloadListItem, MovementPayload, MovementInDbBase
from schemas.romaneio_schema import RomaneioInDbBase, RomaneioUpdate
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
- Para casos de **COLETA** do **APP**, o `product_id` pode ser igual a `0`
- Nesse caso:
    - use `COLLECTED` como `movement_type`

> **Nota:** Use sempre `product_id` quando disponível.
"""

    service = MovementService()
    service_response = await service.create_movement(db=db, payload=payload)
    # Se for um movimento de retorno, verifico se é do arancia e atualizo o romaneio
    if payload.movement_type == 'RETURN':
        origin_item = origin.get(db=db, id=payload.order_origin_id)
        if origin_item and origin_item.origin_name == 'arancia' and origin_item.project_name == 'RETURN':
            # obtenho o romaneio_id e atualizo o status para fechado
            await service.update_rom_by_movement(db=db, romaneio_in=payload.order_number, movement_type=payload.movement_type.value)
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
- Para casos de **COLETA** do **APP**, o `product_id` pode ser igual a `0`
- Nesse caso:
    - use `COLLECTED` como `movement_type`

> **Nota:** Use sempre `product_id` quando disponível.
"""
    if payload.movement_type.value != 'IN':
        for item_payload in payload.item:
            _item = await item_crud.get_last_by_filters(
                db=db,
                filters={
                    'serial': {'operator': '==', 'value': item_payload.serial}
                })
            if not _item:
                raise HTTPException(
                    status_code=400, detail=f"Item com serial {item_payload.serial} não encontrado no sistema. Operação cancelada!")

    service = MovementService()
    items = []
    for item in payload.item:

        item_volume_number = str(
            item.extra_info.get('volume_number', None))
        item_kit_number = str(item.extra_info.get('kit_number', None))
        if item_volume_number == 'None' or item_kit_number == 'None':
            item_volume_number = None if item_volume_number == 'None' else item_volume_number
            item_kit_number = None if item_kit_number == 'None' else item_kit_number
        if not item_volume_number or not item_kit_number:
            item_volume_number = payload.volume_number if not item_volume_number and item_volume_number != 'None' else item_volume_number
            item_kit_number = payload.kit_number if not item_kit_number and item_kit_number != 'None' else item_kit_number

        if not item_volume_number or not item_kit_number:
            raise HTTPException(
                status_code=400, detail="É necessário informar o volume_number e kit_number, seja no payload geral ou em cada item.")

        payload_item = MovementPayload(
            item=item,
            client_name=payload.client_name,
            movement_type=payload.movement_type,
            from_location_id=payload.from_location_id,
            to_location_id=payload.to_location_id,
            order_origin_id=payload.order_origin_id,
            order_number=payload.order_number,
            volume_number=item_volume_number,
            kit_number=item_kit_number,
            created_by=payload.created_by,
            extra_info=payload.extra_info if payload.extra_info else None,
        )

        service_response = await service.create_movement(db=db, payload=payload_item)
        items.append(service_response)

    # Se for um movimento de retorno, verifico se é do arancia e atualizo o romaneio
    if payload.movement_type.value == 'RETURN':
        origin_item = await origin.get(db=db, id=payload.order_origin_id)
        if origin_item and origin_item.origin_name == 'arancia' and origin_item.project_name == 'REVERSA':
            # obtenho o romaneio_id e atualizo o status para fechado
            await service.update_rom_by_movement(db=db, romaneio_in=payload.order_number, movement_type=payload.movement_type.value)
    return items
