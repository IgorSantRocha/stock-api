from typing import Any, List
import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from crud.crud_movement import movement
from crud.crud_movement import movement
from crud.crud_item import item

from schemas.product_schema import ProductCreate, ProductUpdate, ProductInDbBase
from schemas.item_schema import ItemCreate, ItemStatus, ItemUpdate, ItemInDbBase
from schemas.movement_schema import MovementCreate, MovementPayload, MovementInDbBase, MovementType


logger = logging.getLogger(__name__)


class MovementService:
    def _get_status(self, movement_type: MovementType) -> str:
        """Retorna o novo status de um Item baseado no tipo de movimentação."""

        status_map: dict[MovementType, ItemStatus] = {
            MovementType.IN.value: ItemStatus.IN_DEPOT.value,
            MovementType.DELIVERY.value: ItemStatus.WITH_CUSTOMER.value,
            MovementType.TRANSFER.value: ItemStatus.IN_TRANSIT.value,
            MovementType.RETURN.value: ItemStatus.WITH_CLIENT.value,
            MovementType.ADJUST.value: ItemStatus.IN_DEPOT.value,
        }
        result = status_map.get(movement_type)

        # default opcional
        return result

    async def create_movement(self, db: Session, payload: MovementPayload) -> ItemInDbBase:
        """
        1. Verifica se o item já existe, se não existir, cria o item
        2. Cria o movimento
        3. Atualiza o location e o status do item de acordo com o movimento
        4. Retorna o Item para que seja visualizada a sua posição final

        """

        logger.info("Consultando item...")
        _item = await item.get_last_by_filters(
            db=db,
            filters={
                'serial': {'operator': '==', 'value': payload.item.serial}
            })
        if not _item:
            logger.info("Item não encontrado, criando novo item...")
            item_in = ItemCreate(
                product_id=payload.item.product_id,
                serial=payload.item.serial,
                status=self._get_status(payload.movement_type.value),
                extra_info=payload.item.extra_info,
                location_id=payload.to_location_id
            )
            _item = await item.create(db=db, obj_in=item_in)
            logger.info(f"Item criado com ID: {_item.id}")

        logger.info("Criando novo movement...")
        movement_in = MovementCreate(
            movement_type=payload.movement_type,
            item_id=_item.id,
            order_origin_id=payload.order_origin_id,
            from_location_id=payload.from_location_id,
            to_location_id=payload.to_location_id,
            order_number=payload.order_number,
            volume_number=payload.volume_number,
            kit_number=payload.kit_number,
            extra_info=payload.extra_info,
            created_by=payload.created_by
        )
        _movement = await movement.create(db=db, obj_in=movement_in)
        logger.info(f"Movement criado com ID: {_movement.id}")
        logger.info("Atualizando item...")

        item_update = ItemUpdate(
            location_id=payload.to_location_id,
            status=self._get_status(payload.movement_type.value)

        )
        _item = await item.update(db=db, db_obj=_item, obj_in=item_update)
        return _item
