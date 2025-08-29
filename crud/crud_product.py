from crud.baseSync import CRUDBase
from models.product_model import Product as Model
from schemas.product_schema import ProductCreate as SchemaCreate, ProductUpdate as SchemaUpdate


class CRUDItem(CRUDBase[Model, SchemaCreate, SchemaUpdate]):
    pass


product = CRUDItem(Model)
