from crud.baseAsync import CRUDBase
from models.location_model import Location as Model
from schemas.location_schema import LocationCreate as SchemaCreate, LocationUpdate as SchemaUpdate


class CRUDItem(CRUDBase[Model, SchemaCreate, SchemaUpdate]):
    pass


location = CRUDItem(Model)
