from typing import Any, List
import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from crud.crud_romaneio import romaneio_crud_item as romaneio
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
    # Consulta todas as romaneios possíveis
    """
    logger.info("Consultando romaneios...")
    return await romaneio.get_multi(db=db, skip=skip, limit=limit)


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
