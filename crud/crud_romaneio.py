from crud.baseAsync import CRUDBase
from models.romaneio_model import Romaneio as Model
from schemas.romaneio_schema import RomaneioCreate as SchemaCreate, RomaneioUpdate as SchemaUpdate


class CRUDItem(CRUDBase[Model, SchemaCreate, SchemaUpdate]):
    pass


romaneio_crud_item = CRUDItem(Model)
