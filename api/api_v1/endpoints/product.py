from typing import Any, List
import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from crud.crud_product import product
from schemas.product_schema import ProductCreate, ProductUpdate, ProductInDbBase


from api import deps

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/", response_model=List[ProductInDbBase])
async def read_products(
        db: Session = Depends(deps.get_db_psql),
        skip: int = 0,
        limit: int = 100,
) -> Any:
    """
    # Consulta todas as produtos possíveis
    """
    logger.info("Consultando products...")
    return await product.get_multi(db=db, skip=skip, limit=limit)


@router.get("/{client}", response_model=List[ProductInDbBase])
async def read_products(
        client: str,
        db: Session = Depends(deps.get_db_psql)
) -> Any:
    """
    # Consulta todas as produtos possíveis
    """
    logger.info("Consultando products por client...")

    _products = await product.get_multi_filter(db=db, filterby="client_name", filter=client)
    return _products


@router.post("/", response_model=ProductInDbBase)
async def create_product(
        *,
        db: Session = Depends(deps.get_db_psql),
        product_in: ProductCreate,
) -> Any:
    """
    # Cria um novo produto
    """
    # verifica se o produto já existe, se existir, ignora a criação
    existing_product = await product.get_last_by_filters(
        db=db,
        filters={
            'sku': {'operator': '==', 'value': product_in.sku},
            'description': {'operator': '==', 'value': product_in.description}
        }
    )
    if existing_product:
        logger.info("Produto já existe, ignorando criação...")
        return existing_product

    logger.info("Criando novo product...")
    _product = await product.create(db=db, obj_in=product_in)
    return _product


@router.delete(path="/{id}", response_model=ProductInDbBase)
async def delete_product(
        *,
        db: Session = Depends(deps.get_db_psql),
        id: int,
) -> Any:
    """
    # Deleta um produto existente

    ⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️

    ### CUIDADO: Essa ação é irreversível!
    """
    _product = await product.get(db=db, id=id)
    if not _product:
        raise HTTPException(status_code=404, detail="product not found")
    logger.info("Deletando nova product...")
    _product = await product.remove(db=db, id=id)
    return _product
