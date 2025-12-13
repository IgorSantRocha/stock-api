from typing import Any, List
import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from crud.crud_origin import origin
from schemas.origin_schema import OrderOriginCreate, OrderOriginUpdate, OrderOriginInDbBase


from api import deps

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/{client}", response_model=List[OrderOriginInDbBase])
async def read_origins_by_client(
        client: str,
        db: Session = Depends(deps.get_db_psql)

) -> Any:
    """
    # Consulta as origens atreladas ao cliente informado
    """
    logger.info("Consultando origins por client...")
    _origins = await origin.get_multi_filter(db=db, filterby="client.client_code", filter=client)
    return _origins


@router.get("/", response_model=List[OrderOriginInDbBase])
async def read_origins(
        db: Session = Depends(deps.get_db_psql),
        skip: int = 0,
        limit: int = 100,
) -> Any:
    """
    # Consulta todas as origens possíveis
    """
    logger.info("Consultando origins...")
    return await origin.get_multi(db=db, skip=skip, limit=limit)


@router.post("/", response_model=OrderOriginInDbBase)
async def create_origin(
        *,
        db: Session = Depends(deps.get_db_psql),
        origin_in: OrderOriginCreate,
) -> Any:
    """
    # Cria uma nova origem
    """
    logger.info("Criando nova origin...")
    _origin = await origin.create(db=db, obj_in=origin_in)
    return _origin


@router.delete(path="/{id}", response_model=OrderOriginInDbBase)
async def delete_origin(
        *,
        db: Session = Depends(deps.get_db_psql),
        id: int,
) -> Any:
    """
    # Deleta uma origem existente

    ⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️

    ## CUIDADO: Essa ação é irreversível!
    """
    _origin = await origin.get(db=db, id=id)
    if not _origin:
        raise HTTPException(status_code=404, detail="origin not found")
    logger.info("Deletando nova origin...")
    _origin = await origin.remove(db=db, id=id)
    return _origin
# exemplo
