import datetime
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
    last_in_movement_id: Optional[int] = None
    last_out_movement_id: Optional[int] = None
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
    last_in_movement_id: Optional[int] = None
    last_out_movement_id: Optional[int] = None


class ItemProductUpdate(BaseModel):
    product_id: int


class ItemInDbBase(ItemBase):
    id: int


class ItemInDbListBase(BaseModel):
    id: int
    serial: str
    status: ItemStatus = Field(
        ...,
        description=f"Status atual do item. Opções: {[e.value for e in ItemStatus]}",
        example=ItemStatus.IN_DEPOT
    )
    location_name: str
    product_sku: str
    product_description: str
    produtct_category: str
    last_movement_in_date: Optional[datetime.datetime] = None
    stock_type: Optional[str] = None
    extra_info: Optional[dict[str, Any]] = None


class ItemPedidoInDbBase(ItemBase):
    id: int
    in_order_number: str


class Item(ItemInDbBase):
    pass
