from crud.baseAsync import CRUDBase
from models.item_provisional_serial_model import ProvisionalSerialItem as Model
from schemas.item_provisional_serial_schema import (
    ProvisionalSerialCreate as SchemaCreate,
    ProvisionalSerialUpdate as SchemaUpdate)


class CRUDItem(CRUDBase[Model, SchemaCreate, SchemaUpdate]):
    pass


item_provisional_serial_crud = CRUDItem(Model)
