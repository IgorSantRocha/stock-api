from crud.baseAsync import CRUDBase
from models.errors_model import StockErrors as Model
from schemas.errors_stock_schema import StockErrorsCreate as SchemaCreate, StockErrorsUpdate as SchemaUpdate


class CRUDItem(CRUDBase[Model, SchemaCreate, SchemaUpdate]):
    pass


errors_stock_crud = CRUDItem(Model)
