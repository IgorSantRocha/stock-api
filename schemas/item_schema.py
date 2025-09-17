import enum
from typing import Optional, Any
from pydantic import BaseModel, Field


class ItemStatus(enum.Enum):
    # No depósito (Usado em casos de produtos que estão em algum depósito nosso)
    IN_DEPOT = "IN_DEPOT"
    # Em trânsito (Usado em casos de produtos que estão em posse do técnico/Transportadora)
    IN_TRANSIT = "IN_TRANSIT"
    # Com o cliente (Usado em casos onde o item está em posse do contratante ou um de seus representantes)
    WITH_CLIENT = "WITH_CLIENT"
    # Com o cliente final, ou seja, instalado.
    WITH_CUSTOMER = "WITH_CUSTOMER"


class ItemPayload(BaseModel):
    product_id: int
    serial: str
    extra_info: Optional[dict[str, Any]] = None


class ItemBase(BaseModel):
    product_id: int
    serial: str
    status: ItemStatus = Field(
        ...,
        description=f"Status atual do item. Opções: {[e.value for e in ItemStatus]}",
        example=ItemStatus.IN_DEPOT
    )
    extra_info: Optional[dict[str, Any]] = None
    location_id: int
    # Pydantic v2
    model_config = {"from_attributes": True}
    # Se estiver em Pydantic v1, use:
    # class Config:
    #     orm_mode = True


class ItemCreate(ItemBase):
    pass


class ItemUpdate(BaseModel):
    status: str = Field(
        ...,
        description=f"Status atual do item. Opções: {[e.value for e in ItemStatus]}",
        example=ItemStatus.IN_DEPOT
    )
    location_id: int


class ItemInDbBase(ItemBase):
    id: int


class ItemPedidoInDbBase(ItemBase):
    id: int
    in_order_number: str


class Item(ItemInDbBase):
    pass
