from typing import Optional, Any
from pydantic import BaseModel, Field


class ItemBase(BaseModel):
    product_id: Optional[int]
    serial: Optional[str] = None
    status: str = "ATIVO"
    extra_info: Optional[dict[str, Any]] = None

    # Pydantic v2
    model_config = {"from_attributes": True}
    # Se estiver em Pydantic v1, use:
    # class Config:
    #     orm_mode = True


class ItemCreate(ItemBase):
    pass


class ItemUpdate(BaseModel):
    pass  # se quiser "PATCH", deixe todos os campos opcionais aqui


class ItemInDbBase(ItemBase):
    id: int


class Item(ItemInDbBase):
    pass
