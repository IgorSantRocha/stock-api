from typing import Any, List
import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from crud.crud_client import client_crud
from schemas.client_schema import ClientCreateSC, ClientUpdateSC, ClientInDBBaseSC


from api import deps

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/", response_model=List[ClientInDBBaseSC])
async def read_clients(
        db: Session = Depends(deps.get_db_psql),
        skip: int = 0,
        limit: int = 100,
) -> Any:
    """
    # Consulta todas os clientes possíveis
    """
    logger.info("Consultando clients...")
    return await client_crud.get_multi(db=db, skip=skip, limit=limit)


@router.post("/", response_model=ClientInDBBaseSC)
async def create_client(
        *,
        db: Session = Depends(deps.get_db_psql),
        client_in: ClientCreateSC,
) -> Any:
    """
    # Cria um novo cliente
    """
    client_in.client_code = client_in.client_code.lower()
    logger.info("Criando nova client...")
    _client = await client_crud.create(db=db, obj_in=client_in)
    return _client


@router.delete(path="/{id}", response_model=ClientInDBBaseSC)
async def delete_client(
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
        raise HTTPException(status_code=404, detail="client not found")
    logger.info("Deletando nova client...")
    _client = await client_crud.remove(db=db, id=id)
    return _client
# exemplo


@router.put(path="/{id}", response_model=ClientInDBBaseSC)
async def put_client(
        *,
        db: Session = Depends(deps.get_db_psql),
        id: int,
        payload: ClientUpdateSC
) -> Any:
    """
    # Atualiza informações de um produto existente
    ### CUIDADO: Essa ação é irreversível!
    """
    client = await client_crud.get(db=db, id=id)
    if not client:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Cliente {id} não existe")
    payload.client_code = payload.client_code.lower()
    _client = await client_crud.update(db=db, db_obj=client, obj_in=payload)
    return _client
