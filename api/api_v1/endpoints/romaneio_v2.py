from typing import Any, List, Literal
import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from crud.crud_origin import origin
from crud.crud_movement import movement as movement_crud
from crud.crud_romaneio_item import romaneio_crud_item as romaneio_item
from crud.crud_romaneio import romaneio_crud as romaneio
from crud.crud_item import item as item_crud
from crud.crud_client import client_crud
from schemas.item_schema import ItemPayload
from schemas.movement_schema import MovementBase, MovementCreate, MovementPayload
from schemas.romaneio_item_schema import RomaneioItemPayload, RomaneioItemCreate, RomaneioItemInDbBase, RomaneioItemResponse, RomaneioItemUpdateKit
from schemas.romaneio_schema import RomaneioCreateV2, PayloadRomaneioCreateV2, RomaneioFineshedResponse, RomaneioFinisheData, RomaneioInDbBase, RomaneioCreate, RomaneioCreateClient, RomaneioUpdate

from services.romaneio import RomaneioItemService
from services.movement import MovementService
from api import deps

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/", response_model=RomaneioItemResponse)
async def create_romaneio(
        *,
        db: Session = Depends(deps.get_db_psql),
        romaneio_in: PayloadRomaneioCreateV2,
) -> Any:
    """
    # Cria um novo romaneio
    """

    logger.info("Criando novo romaneio...")
    _client = await client_crud.get_first_by_filter(db=db, filterby="client_code", filter=romaneio_in.client_name)
    new_rom = RomaneioCreateV2(
        client_id=_client.id,
        location_id=romaneio_in.location_id,
        created_by=romaneio_in.created_by,
        origin_id=romaneio_in.origin_id,
        destination_id=romaneio_in.destination_id
    )
    _romaneio = await romaneio.create(db=db, obj_in=new_rom)
    service = RomaneioItemService()
    # romaneio_in_str = f"AR{str(_romaneio.id).zfill(5)}"
    existing_romaneio = await service.consulta_romaneio(db=db, romaneio_in=_romaneio.romaneio_number)
    return existing_romaneio


@router.post("/finish/{romaneio_number}", response_model=RomaneioFineshedResponse)
async def finish_romaneio(
        *,
        romaneio_number: str,
        location_id: int,
        finish_data: RomaneioFinisheData,
        db: Session = Depends(deps.get_db_psql)
) -> Any:
    """
    Consulta romaneio_number com base na location
    Se location_id = 0 usa somente o número do romaneio como filto
    Finaliza o romaneio alterando o status para 'FECHADO'
    Gera movimentos de saída para todos os items do romaneio de acordo com o finish_data.movement_type
    Atualiza posição dos itens no estoque
    """
    if finish_data.movement_type.value not in ('RETURN', 'TRANSFER'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tipo de movimentação inválida para finalização de romaneio. Use 'RETURN' ou 'TRANSFER'."
        )
    logger.info("Finalizando romaneio...")
    # service = RomaneioItemService()
    existing_romaneio = await romaneio.get_last_by_filters(
        db=db,
        filters={
            'romaneio_number': {'operator': '==', 'value': romaneio_number},
            'location_id': {'operator': '==', 'value': location_id},
        }
    ) if location_id != 0 else await romaneio.get_last_by_filters(
        db=db,
        filters={
            'romaneio_number': {'operator': '==', 'value': romaneio_number},
        }
    )

    if not existing_romaneio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Romaneio não encontrado")

    if existing_romaneio.status_rom not in ('ABERTO', 'EM PROCESSAMENTO'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=f"Romaneio está com status {existing_romaneio.status_rom}")

    # atualiza o status do romaneio para FECHADO
    romaneio_update = RomaneioUpdate(
        status_rom='EM PROCESSAMENTO',
        update_by=finish_data.finished_by,
        updated_at=finish_data.finished_at
    )
    await romaneio.update(db=db, db_obj=existing_romaneio, obj_in=romaneio_update)

    # gera movimentos de saída para todos os items do romaneio
    romaneio_list = await romaneio_item.get_multi_filter(db=db, filterby="romaneio_id", filter=existing_romaneio.id)

    new_order_origin_id = await origin.get_last_by_filters(
        db=db,
        filters={
            'origin_name': {'operator': '==', 'value': 'arancia'},
            'project_name': {'operator': '==', 'value': 'REVERSA'},
            'client_id': {'operator': '==', 'value': existing_romaneio.client_id}
        }
    )

    movement_service = MovementService()
    for item_rom in romaneio_list:
        # last_movement = await movement_crud.get_last_movement_by_item(db=db, item_id=item.item_id)
        # if not last_movement:
        #     raise HTTPException(
        #         status_code=status.HTTP_404_NOT_FOUND,
        #         detail=f"Item {item.item_id} não possui movimento de entrada registrado.",
        #     )

        item_data = ItemPayload(
            product_id=item_rom.item.product_id,
            serial=item_rom.item.serial
        )

        _extra_info = {
            "external_order_number": finish_data.external_order_number
        } if finish_data.external_order_number else None
        item_movement = MovementPayload(
            item=item_data,
            client_name=existing_romaneio.client.client_code,
            movement_type=finish_data.movement_type,
            from_location_id=existing_romaneio.origin_id,
            to_location_id=existing_romaneio.destination_id,
            order_origin_id=new_order_origin_id.id if new_order_origin_id else None,
            order_number=romaneio_number,
            volume_number=item_rom.volume_number,
            kit_number=item_rom.kit_number,
            created_by=finish_data.finished_by,
            extra_info=_extra_info
        )

        await movement_service.create_movement(
            db=db,
            payload=item_movement
        )
    # atualiza o status do romaneio para FECHADO
    await movement_service.update_rom_by_movement(
        db=db,
        romaneio_in=romaneio_number,
        movement_type=finish_data.movement_type.value
    )
    return RomaneioFineshedResponse(
        romaneio_number=romaneio_number,
        status_rom="FECHADO",
        description="Romaneio finalizado com sucesso.",
        finished_at=finish_data.finished_at
    )
