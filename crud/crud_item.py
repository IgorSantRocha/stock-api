from crud.baseSync import CRUDBase
from models.item_model import Item
from schemas.item_schema import ItemCreate, ItemUpdate


class CRUDItem(CRUDBase[Item, ItemCreate, ItemUpdate]):
    pass


item = CRUDItem(Item)
