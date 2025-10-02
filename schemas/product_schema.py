from typing import Optional, Any
from pydantic import BaseModel, Field


class ProductBase(BaseModel):
    sku: str = Field(..., description="Código único do produto (SKU). Pode receber o MATNR",
                     example="605043")
    description: str = Field(..., description="Descrição detalhada ou modelo do produto",
                             example="PinPad Verifone VX820")
    category: Optional[str] = Field(
        None, description="Categoria do produto (ex.: POS, Modem, PinPad)", example="POS")

    client_id: int = Field(...,
                           description="Id do cliente associado ao produto",
                           example="cielo = 1")

    created_by: str = Field(...,
                            description="Username/Sysname de criação",
                            example="ARC000X")

    extra_info: Optional[dict[str, Any]] = Field(
        None,
        description="Informações adicionais em formato JSON",
        example={
            "measures": {
                "width": 22.4,
                "weight": 0.737,
                "length": 18.3,
                "height": 6.7,
                "quantity": 1,
                "price": 150.55
            }
        }
    )

    model_config = {"from_attributes": True}


class ProductCreate(ProductBase):
    """Schema usado na criação de um produto"""
    pass


class ProductUpdate(ProductBase):
    """Schema usado na atualização de um produto"""
    pass  # se preferir PATCH, torne os campos opcionais aqui


class ProductInDbBase(ProductBase):
    id: int = Field(...,
                    description="ID interno do produto no banco de dados", example=1)


class Product(ProductInDbBase):
    """Schema retornado pela API ao consultar um produto"""
    pass
