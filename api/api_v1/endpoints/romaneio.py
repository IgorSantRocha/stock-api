from typing import Any, List
import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from crud.crud_movement import movement as movement_crud
from crud.crud_romaneio_item import romaneio_crud_item as romaneio_item
from crud.crud_romaneio import romaneio_crud as romaneio
from crud.crud_item import item as item_crud
from schemas.romaneio_item_schema import RomaneioItemPayload, RomaneioItemCreate, RomaneioItemInDbBase, RomaneioItemResponse
from schemas.romaneio_schema import RomaneioCreate, RomaneioUpdate, RomaneioInDbBase

from services.romaneio import RomaneioItemService

from api import deps

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/", response_model=List[RomaneioInDbBase])
async def read_romaneios(
        db: Session = Depends(deps.get_db_psql),
        skip: int = 0,
        limit: int = 100,
) -> Any:
    """
    # Consulta todas as romaneios possíveis, com paginação
    """
    logger.info("Consultando romaneios...")
    return await romaneio.get_multi(db=db, skip=skip, limit=limit)


@router.get("/{romaneio_in}", response_model=RomaneioItemResponse)
async def read_romaneio(
        romaneio_in: str,
        db: Session = Depends(deps.get_db_psql)
) -> Any:
    """
    # Consulta o romaneio informado
    * Recebe o `romaneio_in` (str) no formato: AR00003 e extrai o ID desse romaneio (remove o AR e os zeros à esquerda)
    * Se o Romaneio não existe, retorna 404

    """
    service = RomaneioItemService()

    existing_romaneio = await service.consulta_romaneio(db=db, romaneio_in=romaneio_in)
    return existing_romaneio


@router.post("/insert-items/{romaneio_in}", response_model=RomaneioItemResponse)
async def insert_items_romaneio(
        romaneio_in: str,
        item: RomaneioItemPayload,
        db: Session = Depends(deps.get_db_psql)):
    """
    # Insere os itens no romaneio informado

    ## Validações de romaneio
    * Recebe o `romaneio_in` (str) no formato: AR00003 e extrai o ID desse romaneio (remove o AR e os zeros à esquerda)
    * Se o Romaneio não existe, retorna 404

    ## Validações de item
    * Consulta o item pelo serial e client
    * Se o último movemento do item não for de entrada(movement_type=IN), retorna um erro

    ## Validações para vincular item e romaneio
    * Se o item já estiver no romaneio, ignora a inserção
    * Se o item estiver em outro romaneio ativo, retorna um erro
    * Se o item estiver em outro romaneio inativo, permite a inserção
    * Atualiza o item com o romaneio_id
    """
    service = RomaneioItemService()

    romaneio_list = await service.insere_novo_item(db=db, romaneio_in=romaneio_in, item=item)
    return romaneio_list


@router.post("/", response_model=RomaneioInDbBase)
async def create_romaneio(
        *,
        db: Session = Depends(deps.get_db_psql),
        romaneio_in: RomaneioCreate,
) -> Any:
    """
    # Cria um novo romaneio
    """

    logger.info("Criando novo romaneio...")
    _romaneio = await romaneio.create(db=db, obj_in=romaneio_in)
    return _romaneio


@router.put(path="/{id}", response_model=RomaneioInDbBase)
async def put_romaneio(
        *,
        db: Session = Depends(deps.get_db_psql),
        id: int,
        payload: RomaneioUpdate
) -> Any:
    """
    # Atualiza informações de um romaneio existente
    ### CUIDADO: Essa ação é irreversível!
    """
    _romaneio = await romaneio.get(db=db, id=id)
    if not _romaneio:
        raise HTTPException(status_code=404, detail="romaneio not found")

    if _romaneio.created_by and not _romaneio.created_by.startswith('ARC'):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Não é permitido alterar este romaneio")

    logger.info("Deletando nova romaneio...")
    _romaneio = await romaneio.update(db=db, db_obj=_romaneio, obj_in=payload)
    return _romaneio


@router.delete(path="/{romaneio_in}/{id}", response_model=RomaneioItemResponse)
async def delete_item_rom(
        romaneio_in: str,
        serial: str,
        db: Session = Depends(deps.get_db_psql),
) -> Any:
    """
    # Deleta um item do romaneio de acordo com o serial

    ⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️

    ### CUIDADO: Essa ação é irreversível!
    """

    item = await item_crud.get_first_by_filter(
        db=db, filterby="serial", filter=serial)
    item_id = item.id
    _romaneio_item = await romaneio_item.get_last_by_filters(
        db=db,
        filters={
            'item_id': {'operator': '==', 'value': item_id},
            'romaneio.id': {'operator': '==', 'value': int(romaneio_in.replace('AR', '').lstrip('0'))},
        }
    )
    if not _romaneio_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Serial ou romaneio não existem")

    if _romaneio_item.romaneio.status_rom != 'ABERTO':
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Romaneio com status {_romaneio_item.romaneio.status_rom} (Só é permitido remover itens de romaneios com status 'ABERTO')",
        )

    logger.info("Deletando nova product...")
    _romaneio_item = await romaneio_item.remove(db=db, id=_romaneio_item.id)

    service = RomaneioItemService()
    existing_romaneio = await service.consulta_romaneio(db=db, romaneio_in=romaneio_in)
    if not existing_romaneio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="romaneio not found")

    return existing_romaneio
