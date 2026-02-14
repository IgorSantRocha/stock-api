

from fastapi import HTTPException, status
from schemas.errors_stock_schema import StockErrorsCreate
from sqlalchemy.orm import Session
from crud.crud_errors_stock import errors_stock_crud


class ItemService:

    async def salva_erro(self, db: Session, erro: StockErrorsCreate):
        try:
            return await errors_stock_crud.create(db=db, obj_in=erro)
        except Exception as e:
            print(f"Erro ao salvar o erro: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "error": f"Erro ao salvar o erro: {e}"
                }
            )
