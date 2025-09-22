
from typing import Any, List
import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from crud.crud_movement import movement as movement_crud
from crud.crud_romaneio_item import romaneio_crud_item as romaneio_item
from crud.crud_romaneio import romaneio_crud as romaneio
from schemas.romaneio_item_schema import RomaneioItemPayload, RomaneioItemCreate, RomaneioItemInDbBase
from schemas.romaneio_item_schema import RomaneioItemResponse, RomaneioItemVolum, RomaneioItemKit
from schemas.romaneio_schema import RomaneioCreate, RomaneioUpdate, RomaneioInDbBase


from api import deps

router = APIRouter()
logger = logging.getLogger(__name__)


class RomaneioItemService:
    def build_romaneio_response(self, romaneio_list, status_rom=None):
        volumes_dict = {}

        for idx, item in enumerate(romaneio_list, start=1):
            vol_num = int(item.volume_number)
            kit_num = int(item.kit_number) if item.kit_number else idx

            if vol_num not in volumes_dict:
                volumes_dict[vol_num] = {}

            if kit_num not in volumes_dict[vol_num]:
                volumes_dict[vol_num][kit_num] = []

            item_volume = RomaneioItemKit(
                kit_number=str(item.kit_number),
                serial=item.item.serial,
                order_number=item.order_number,
                created_by=item.created_by,
                created_at=item.created_at

            )
            volumes_dict[vol_num][kit_num].append(item_volume)

        volumes = []
        for vol_num, kits_dict in volumes_dict.items():
            kits = []
            for kit_num, kit_items in kits_dict.items():
                kits.extend(kit_items)
            volumes.append(RomaneioItemVolum(
                volum_number=str(vol_num), kits=kits))

        return RomaneioItemResponse(
            romaneio=str(romaneio_list[0].romaneio_id),
            status=status_rom,
            volums=volumes
        )

    async def insere_novo_item(self, db: Session, romaneio_in: str, item: RomaneioItemPayload):
        logger.info("Consulta o romaneio")
        romaneio_id = int(romaneio_in.replace('AR', '').lstrip('0'))
        existing_romaneio = await romaneio.get_last_by_filters(
            db=db,
            filters={
                'id': {'operator': '==', 'value': romaneio_id},
            }
        )
        # Se o romaneio não existir, retorna um erro
        if not existing_romaneio:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="romaneio not found")

        if existing_romaneio.status_rom != 'ABERTO':
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Romaneio inativo (Só é permitido inserir itens em romaneios com status 'ABERTO')",
            )

        logger.info("Consulta o item pelo serial e client")
        last_movement = await movement_crud.get_last_by_filters(
            db=db,
            filters={
                'item.serial': {'operator': '==', 'value': item.serial},
                'item.product.client_name': {'operator': '==', 'value': item.client},
                'item.status': {'operator': '==', 'value': 'IN_DEPOT'},
                'item.location_id': {'operator': '==', 'value': item.location_id}
            }
        )

        if not last_movement:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Item not found (O serial informado não existe, não pertence a este cliente ou não está com status 'IN_DEPOT')",
            )

        if last_movement.movement_type != 'IN':
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Item sem pedido (O item não possui um movimento de entrada associado)",
            )

        # inicio as validações de romaneio
        logger.info("Iniciando as validações de romaneio")

        existing_romaneio_item = await romaneio_item.get_last_by_filters(
            db=db,
            filters={
                'romaneio_id': {'operator': '==', 'value': existing_romaneio.id},
                'item_id': {'operator': '==', 'value': last_movement.item_id}
            })
        # verifico se o item está atrelado a outro romaneio em aberto
        existing_outher_romaneio_item = await romaneio_item.get_last_by_filters(
            db=db,
            filters={
                'item_id': {'operator': '==', 'value': last_movement.item_id},
                'romaneio.status_rom': {'operator': '==', 'value': 'ABERTO'}
            })
        if existing_outher_romaneio_item:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Item {last_movement.item.serial} já atrelado a outro romaneio em aberto (Romaneio: AR{str(existing_outher_romaneio_item.romaneio_id).zfill(6)})",
            )
        if not existing_romaneio_item:
            obj_romaneio_item = RomaneioItemCreate(
                romaneio_id=existing_romaneio.id,
                item_id=last_movement.item_id,
                created_by=item.create_by,
                kit_number=item.kit_number,
                volume_number=item.volume_number,
                order_number=last_movement.order_number
            )

            new_obj = await romaneio_item.create(db=db, obj_in=obj_romaneio_item)

        # consulto o romaneio atualizado e retorno a lista de items atrelados a ele
        romaneio_list = await romaneio_item.get_multi_filter(db=db, filterby="romaneio_id", filter=existing_romaneio.id)
        return self.build_romaneio_response(romaneio_list, existing_romaneio.status_rom)

    async def consulta_romaneio(self, db: Session, romaneio_in: str):
        logger.info("Consulta o romaneio")
        romaneio_id = int(romaneio_in.replace('AR', '').lstrip('0'))
        existing_romaneio = await romaneio.get_last_by_filters(
            db=db,
            filters={
                'id': {'operator': '==', 'value': romaneio_id},
            }
        )
        # Se o romaneio não existir, retorna um erro
        if not existing_romaneio:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="romaneio not found")
        # consulto o romaneio atualizado e retorno a lista de items atrelados a ele
        romaneio_list = await romaneio_item.get_multi_filter(db=db, filterby="romaneio_id", filter=romaneio_id)
        if not romaneio_list:
            return RomaneioItemResponse(
                romaneio=str(romaneio_id),
                status=existing_romaneio.status_rom,
                volums=[]
            )
        return self.build_romaneio_response(romaneio_list, existing_romaneio.status_rom)
