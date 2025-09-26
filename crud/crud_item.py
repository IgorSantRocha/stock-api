from typing import Any, Dict, List, Optional
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from crud.baseAsync import CRUDBase
from models.item_model import Item
from models.product_model import Product   # ajuste o caminho se necessário
from models.location_model import Location  # ajuste o caminho se necessário
from schemas.item_schema import ItemCreate, ItemUpdate


class CRUDItem(CRUDBase[Item, ItemCreate, ItemUpdate]):
    pass


# instância exportada
item = CRUDItem(Item)
