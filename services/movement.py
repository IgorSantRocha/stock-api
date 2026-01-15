from typing import Any, List
import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from core.request import RequestClient

from crud.crud_product import product
from crud.crud_movement import movement
from crud.crud_item import item
from crud.crud_romaneio import romaneio_crud
from crud.crud_romaneio_item import romaneio_crud_item
from crud.crud_item_provisional_serial import item_provisional_serial_crud
from crud.crud_origin import origin as crud_origin

from schemas.product_schema import ProductCreate, ProductUpdate, ProductInDbBase
from schemas.item_schema import ItemCreate, ItemProductUpdate, ItemStatus, ItemUpdate, ItemInDbBase
from schemas.movement_schema import MovementCreate, MovementPayload, MovementInDbBase, MovementType
from schemas.romaneio_schema import RomaneioUpdate
from schemas.item_provisional_serial_schema import ProvisionalSerialCreate, ProvisionalSerialUpdate, ProvisionalSerialInDbBase
from schemas.origin_schema import OrderOriginBase

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
            MovementType.COLLECTED.value: ItemStatus.IN_TRANSIT.value,
        }
        result = status_map.get(movement_type)

        # default opcional
        return result

    async def update_rom_by_movement(self, db: Session, romaneio_in: str, movement_type: str) -> None:
        """
        Atualiza o status do romaneio para 'FECHADO' se todos os itens estiverem com status 'WITH_CUSTOMER'
        """
        item_status_required = self._get_status(movement_type)
        if romaneio_in.startswith('AR1'):
            romaneio_id = int(romaneio_in[5:].lstrip('0'))
        else:
            romaneio_id = int(romaneio_in[3:].lstrip('0'))

        _romaneio = await romaneio_crud.get(db=db, id=romaneio_id)
        if not _romaneio:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='Romaneio não encontrado.'
            )
        _items = await romaneio_crud_item.get_multi_filter(
            db=db,
            filterby='romaneio_id',
            filter=romaneio_id
        )
        if not _items:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='Nenhum item encontrado para esse romaneio.'
            )
        all_with_customer = True
        for rom_item in _items:
            _item = await item.get(db=db, id=rom_item.item_id)
            if _item.status != item_status_required:
                all_with_customer = False
                break
        if all_with_customer and _romaneio.status_rom != 'FECHADO':
            rom_update = RomaneioUpdate(
                status_rom='FECHADO'
            )
            _romaneio = await romaneio_crud.update(db=db, db_obj=_romaneio, obj_in=rom_update)

        return _romaneio

    async def create_provisional_serial(self, db: Session, payload: MovementPayload) -> ProvisionalSerialInDbBase:
        """
        Cria uma Serial provisória para o item.
        """
        logger.info("Criando Serial provisória...")
        # Cria o Serial provisório
        provisional_serial_in = ProvisionalSerialCreate(
            old_serial_number=payload.item.serial,
            created_by=payload.created_by,
            reason='Serial não encontrado na Consulta Sincrona.'
        )
        _provisional_serial = await item_provisional_serial_crud.create(db=db, obj_in=provisional_serial_in)
        logger.info(
            f"Serial provisória criada com ID: {_provisional_serial.id}")
        return _provisional_serial

    async def create_movement(self, db: Session, payload: MovementPayload) -> ItemInDbBase:
        """
        0. Se o product_id do item estiver como zero e o cliente for Cielo. Tento localizar o produto, se não conseguir, retorno um erro.
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

        if not _item and payload.movement_type.value not in ['IN', 'COLLECTED']:
            raise HTTPException(
                status_code=status.HTTP_424_FAILED_DEPENDENCY,
                detail=f'Item {payload.item.serial} não encontrado. Para movimentações diferentes de IN, o item deve existir.'
            )
        if payload.movement_type.value not in ['IN', 'COLLECTED'] and _item.status != 'IN_DEPOT':
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f'Item ({_item.serial}) com status ({_item.status}) inválido para esta movimentação.'
            )

        if not _item:
            if payload.client_name == 'cielo' and not payload.item.serial.startswith('ILG'):
                # Vou tentar localizar o serial na consulta síncrona da Cielo e pegar as informações do produto
                request_data = {"SERGE": payload.item.serial}

                request = RequestClient(
                    method='POST',
                    headers={
                        "Content-Type": 'application/json'},
                    request_data=request_data,
                    url='http://192.168.0.214/IntegrationXmlAPI/api/v1/clo/sincrona/'
                )
                try:
                    result = await request.send_api_request()
                except Exception as e:
                    result = False
                    product_item = await product.get(
                        db=db,
                        id=payload.item.product_id
                    )
                    if product_item.category != 'CHIP':
                        # cria serial provisório e estoura erro adicionando no detail um dicioário com o erro e o serial provisório
                        logger.error(f"Erro na consulta síncrona: {e}")
                        _provisional_serial = await self.create_provisional_serial(db=db, payload=payload)
                        raise HTTPException(
                            status_code=status.HTTP_424_FAILED_DEPENDENCY,
                            detail={
                                "error": f"Erro na consulta síncrona: {e}",
                                "provisional_serial": _provisional_serial.new_serial_number
                            }
                        )

                if result:
                    if payload.item.extra_info is None:
                        payload.item.extra_info = {}

                    payload.item.extra_info['consulta_sincrona'] = result

                # Se achar, consulto o produto pelo sku pra ver se tem cadastro, se não tiver, crio
                if result:
                    _product = await product.get_last_by_filters(
                        db=db,
                        filters={
                            'sku': {'operator': '==', 'value': result['MATNR']}
                        })
                    if not _product:
                        product_in = ProductCreate(
                            category=result['ZTIPO'],
                            client_id=1,
                            description=result['SHTXT'],
                            sku=result['MATNR'],
                            created_by='SAP',
                            extra_info={
                                "measures": {
                                    "width": 22.4,
                                    "weight": 0.737,
                                    "length": 18.3,
                                    "height": 6.7,
                                    "quantity": 1,
                                    "price": 150.55
                                },
                                "alert": "Produto criado automaticamente via integração com o SAP."
                            }
                        )
                        _product = await product.create(db=db, obj_in=product_in)

                    payload.item.product_id = _product.id

            if payload.item.product_id == 0 and payload.movement_type.value != 'COLLECTED':
                raise HTTPException(
                    status_code=status.HTTP_424_FAILED_DEPENDENCY,
                    detail=f'Para movimentações {payload.movement_type}, o product_id deve ser informado.')

            logger.info("Item não encontrado, criando novo item...")
            _status = str(self._get_status(payload.movement_type.value))
            item_in = ItemCreate(
                product_id=payload.item.product_id if payload.item.product_id != 0 else None,
                serial=payload.item.serial,
                status=_status,
                extra_info=payload.item.extra_info,
                location_id=payload.to_location_id if payload.to_location_id else payload.from_location_id,
            )

            _item = await item.create(db=db, obj_in=item_in)
            logger.info(f"Item criado com ID: {_item.id}")
            # verifico se o item criado era um serial provisório, se sim. Atualizo na tabela de controle com o item_id
            if payload.item.serial.startswith('ILG'):
                _provisional_serial = await item_provisional_serial_crud.get_last_by_filters(
                    db=db,
                    filters={
                        'new_serial_number': {'operator': '==', 'value': payload.item.serial}
                    })
                if _provisional_serial:
                    provisional_serial_update = ProvisionalSerialUpdate(
                        item_id=_item.id
                    )
                    _provisional_serial = await item_provisional_serial_crud.update(
                        db=db,
                        db_obj=_provisional_serial,
                        obj_in=provisional_serial_update
                    )
                old_order_origin = await crud_origin.get(db=db, id=payload.order_origin_id)
                new_order_origin_id = await crud_origin.get_last_by_filters(
                    db=db,
                    filters={
                        'origin_name': {'operator': '==', 'value': old_order_origin.origin_name},
                        'project_name': {'operator': '==', 'value': old_order_origin.project_name},
                        'client_id': {'operator': '==', 'value': old_order_origin.client_id},
                        'stock_type': {'operator': '==', 'value': 'Aguardando Reversa (Seriais Provisórios)'},
                    }
                )
                payload.order_origin_id = new_order_origin_id.id

        logger.info("Criando novo movement...")
        movement_in = MovementCreate(
            movement_type=payload.movement_type,
            item_id=_item.id,
            order_origin_id=payload.order_origin_id,
            from_location_id=payload.from_location_id,
            to_location_id=payload.to_location_id if payload.to_location_id else None,
            order_number=payload.order_number,
            volume_number=payload.volume_number,
            kit_number=payload.kit_number,
            extra_info=payload.extra_info,
            created_by=payload.created_by
        )
        _movement = await movement.create(db=db, obj_in=movement_in)
        logger.info(f"Movement criado com ID: {_movement.id}")
        logger.info("Atualizando item...")

        if payload.movement_type.value == 'IN':
            last_in_movement_id = _movement.id
        else:
            last_in_movement_id = _item.last_in_movement_id

        if payload.movement_type.value != 'IN':
            last_out_movement_id = _movement.id
        else:
            last_out_movement_id = _item.last_out_movement_id

        if _item.product_id is None and payload.item.product_id and payload.item.product_id != 0:
            item_product_update = ItemProductUpdate(
                product_id=payload.item.product_id
            )
            _item = await item.update(db=db, db_obj=_item, obj_in=item_product_update)

        item_update = ItemUpdate(
            location_id=payload.to_location_id if payload.to_location_id else payload.from_location_id,
            status=self._get_status(payload.movement_type.value),
            last_in_movement_id=last_in_movement_id,
            last_out_movement_id=last_out_movement_id
        )
        _item = await item.update(db=db, db_obj=_item, obj_in=item_update)

        return _item
