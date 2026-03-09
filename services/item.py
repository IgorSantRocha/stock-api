

from fastapi import HTTPException, status
from schemas.errors_stock_schema import StockErrorsCreate
from sqlalchemy.orm import Session
from crud.crud_errors_stock import errors_stock_crud
from collections import defaultdict
from schemas.product_schema import VolumeProductSchema


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

    def build_volume_product_array(self, items):

        agrupado = defaultdict(lambda: {
            "itemDescription": None,
            "ncmCode": None,
            "quantity": 0,
            "unitPrice": 0,
            "additionalProductInfo": None
        })

        for item in items:

            if not item.product:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Produto com ID {item.product_id} não encontrado."
                )

            key = item.product_id

            descricao = item.product.description

            ncm = None
            unit_price = 0
            info = None

            if item.product.extra_info:
                ncm = item.product.extra_info.get("ncmCode")
                measures = item.product.extra_info.get("measures", {})
                unit_price = measures.get("price", 0)
                info = item.product.extra_info.get("additionalInfo")

            agrupado[key]["itemDescription"] = descricao
            agrupado[key]["ncmCode"] = ncm or "00000000"
            agrupado[key]["unitPrice"] = unit_price or 0
            agrupado[key]["additionalProductInfo"] = info

            agrupado[key]["quantity"] += 1

        volumeProductArray = []

        for g in agrupado.values():

            total = g["quantity"] * g["unitPrice"]

            volumeProductArray.append(
                VolumeProductSchema(
                    itemDescription=g["itemDescription"],
                    ncmCode=g["ncmCode"],
                    quantity=g["quantity"],
                    unitPrice=g["unitPrice"],
                    totalPrice=total,
                    additionalProductInfo=g["additionalProductInfo"] or ''
                )
            )

        return volumeProductArray
