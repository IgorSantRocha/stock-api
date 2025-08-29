from crud.baseSync import CRUDBase
from models.movement_model import Movement as Model
from schemas.movement_schema import MovementCreate as SchemaCreate, MovementUpdate as SchemaUpdate


class CRUDItem(CRUDBase[Model, SchemaCreate, SchemaUpdate]):
    pass


movement = CRUDItem(Model)
