from crud.baseAsync import CRUDBase
from models.romaneio_item_model import RomaneioItem as Model
from schemas.romaneio_item_schema import RomaneioItemCreate as SchemaCreate, RomaneioItemUpdate as SchemaUpdate


class CRUDItem(CRUDBase[Model, SchemaCreate, SchemaUpdate]):
    pass


romaneio_crud_item = CRUDItem(Model)
