from typing import Any, List
import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from crud.crud_client import client_crud
from schemas.client_schema import ClientCreateSC, ClientUpdateSC, ClientInDBBaseSC


from api import deps

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/", response_model=List[ClientInDBBaseSC])
async def read_origins(
        db: Session = Depends(deps.get_db_psql),
        skip: int = 0,
        limit: int = 100,
) -> Any:
    """
    # Consulta todas os clientes possíveis
    """
    logger.info("Consultando origins...")
    return await client_crud.get_multi(db=db, skip=skip, limit=limit)


@router.post("/", response_model=ClientInDBBaseSC)
async def create_origin(
        *,
        db: Session = Depends(deps.get_db_psql),
        origin_in: ClientCreateSC,
) -> Any:
    """
    # Cria um novo cliente
    """
    logger.info("Criando nova origin...")
    _client = await client_crud.create(db=db, obj_in=origin_in)
    return _client


@router.delete(path="/{id}", response_model=ClientInDBBaseSC)
async def delete_origin(
        *,
        db: Session = Depends(deps.get_db_psql),
        id: int,
) -> Any:
    """
    # Deleta um cliente existente

    ⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️

    ## CUIDADO: Essa ação é irreversível!
    """
    _client = await client_crud.get(db=db, id=id)
    if not _client:
        raise HTTPException(status_code=404, detail="origin not found")
    logger.info("Deletando nova origin...")
    _client = await client_crud.remove(db=db, id=id)
    return _client
# exemplo
