from typing import Optional, Any
from pydantic import BaseModel


class ProductBase(BaseModel):
    sku: str
    description: str
    category: Optional[str] = None
    extra_info: Optional[dict[str, Any]] = None

    # Pydantic v2
    model_config = {"from_attributes": True}
    # Se estiver em Pydantic v1:
    # class Config:
    #     orm_mode = True


class ProductCreate(ProductBase):
    pass


class ProductUpdate(ProductBase):
    pass  # se preferir PATCH, torne os campos opcionais aqui


class ProductInDbBase(ProductBase):
    id: int


class Product(ProductInDbBase):
    pass
