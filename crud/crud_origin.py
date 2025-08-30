from crud.baseAsync import CRUDBase
from models.origin_model import OrderOrigin as Model
from schemas.origin_schema import (OrderOriginCreate as SchemaCreate,
                                   OrderOriginUpdate as SchemaUpdate)


class CRUDItem(CRUDBase[Model, SchemaCreate, SchemaUpdate]):
    pass


origin = CRUDItem(Model)
