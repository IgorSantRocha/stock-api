from typing import Any, List
import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from crud.crud_item_provisional_serial import item_provisional_serial_crud
from schemas.item_provisional_serial_schema import ProvisionalSerialCreate, ProvisionalSerialUpdate, ProvisionalSerialInDbBase


from api import deps

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/list", response_model=List[ProvisionalSerialInDbBase])
async def read_provisional_serials(
        db: Session = Depends(deps.get_db_psql),
        skip: int = 0,
        limit: int = 100,
) -> Any:
    """
    # Consulta todas as provisional_serials possíveis
    """
    logger.info("Consultando Serial provisório...")
    return await item_provisional_serial_crud.get_multi(db=db, skip=skip, limit=limit)


@router.get("/{id}", response_model=ProvisionalSerialInDbBase)
async def read_provisional_serial_by_id(
        id: int,
        db: Session = Depends(deps.get_db_psql)

) -> Any:
    """
    # Consulta as Serial provisório atrelado ao id informado
    """
    logger.info("Consultando Seriais provisórios por client...")
    _provisional_serial = await item_provisional_serial_crud.get(db=db, id=id)
    return _provisional_serial


@router.get("/list/old_Serial/{old_serial}", response_model=List[ProvisionalSerialInDbBase])
async def read_provisional_serial_by_old_serial(
        old_serial: str,
        db: Session = Depends(deps.get_db_psql)

) -> Any:
    """
    # Consulta as Seriais provisórios atreladas ao old_serial informado
    """
    logger.info("Consultando Seriais provisórios por client...")
    _provisional_serial = await item_provisional_serial_crud.get_multi_filter(
        db=db, filterby="old_serial_number", filter=old_serial
    )
    return _provisional_serial


@router.post("/", response_model=ProvisionalSerialInDbBase)
async def create_provisional_serial(
        *,
        db: Session = Depends(deps.get_db_psql),
        origin_in: ProvisionalSerialCreate,
) -> Any:
    """
    # Cria uma nova origem
    """
    logger.info("Criando nova Serial provisório...")
    _provisional_serial = await item_provisional_serial_crud.create(db=db, obj_in=origin_in)
    return _provisional_serial


@router.put("/{id}", response_model=ProvisionalSerialInDbBase)
async def update_provisional_serial(
        *,
        db: Session = Depends(deps.get_db_psql),
        id: int,
        provisional_serial_in: ProvisionalSerialUpdate,
) -> Any:
    """
    # Atualiza uma Serial provisório existente
    """
    logger.info("Atualizando Serial provisório...")
    _provisional_serial = await item_provisional_serial_crud.get(db=db, id=id)
    if not _provisional_serial:
        raise HTTPException(
            status_code=404, detail="Provisional Serial not found")
    _provisional_serial = await item_provisional_serial_crud.update(
        db=db,
        db_obj=_provisional_serial,
        obj_in=provisional_serial_in
    )
    return _provisional_serial
