from typing import Any, List
import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from crud.crud_movement import movement as movement_crud
from crud.crud_item import item as item_crud
from crud.crud_romaneio import romaneio_crud as romaneio
from schemas.romaneio_item_schema import RomaneioItemPayload
from schemas.romaneio_schema import RomaneioCreate, RomaneioUpdate, RomaneioInDbBase


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


@router.get("/{romaneio_in}", response_model=RomaneioInDbBase)
async def read_romaneio(
        romaneio_in: str,
        db: Session = Depends(deps.get_db_psql)
) -> Any:
    """
    # Consulta o romaneio informado
    * Recebe o `romaneio_in` (str) no formato: AR00003 e extrai o ID desse romaneio (remove o AR e os zeros à esquerda)
    * Se o Romaneio não existe, retorna 404

    """
    logger.info("Consultando romaneio...")
    romaneio_id = int(romaneio_in.replace('AR', '').lstrip('0'))
    existing_romaneio = await romaneio.get_last_by_filters(
        db=db,
        filters={
            'id': {'operator': '==', 'value': romaneio_id},
        }
    )
    if not existing_romaneio:
        raise HTTPException(status_code=404, detail="romaneio not found")

    return existing_romaneio


@router.post("/insert-items/{romaneio_in}", response_model=RomaneioInDbBase)
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

    return ''


@router.post("/{romaneio}", response_model=RomaneioInDbBase)
async def create_romaneio(
        romaneio_in: str,
        db: Session = Depends(deps.get_db_psql),

) -> Any:
    # Recebe o romaneio no formato: AR00003 e extrai o ID desse romaneio (remove o AR e os zeros à esquerda)

    romaneio_id = int(romaneio_in.replace('AR', '').lstrip('0'))

    existing_romaneio = await romaneio.get_last_by_filters(
        db=db,
        filters={
            'id': {'operator': '==', 'value': romaneio_id},
        }
    )
    if existing_romaneio:
        logger.info("Romaneio já existe, ignorando criação...")
        return existing_romaneio

    logger.info("Romaneio não existe, criando novo romaneio...")
    _romaneio = await romaneio.create(db=db, obj_in=RomaneioCreate(id=romaneio_id, status_rom='ATIVO',
                                                                   item_id=0, volume_number='',
                                                                   kit_number='', created_by='ARC'))

    return ''


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
