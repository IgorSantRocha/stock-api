import datetime
import enum
from typing import Optional, Any
from zoneinfo import ZoneInfo
from pydantic import BaseModel, Field, field_serializer, model_validator


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
    product_id: Optional[int] = None
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


class ItemCreate(BaseModel):
    product_id: Optional[int] = None
    serial: str
    status: str = Field(
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
    id: int

    @field_serializer("last_movement_in_date",  when_used="always")
    def serialize_dt(self, dt: datetime.datetime | None):
        if dt is None:
            return None
        if dt.tzinfo is None:
            # se vier naive, assume que está em UTC
            dt = dt.replace(tzinfo=datetime.timezone.utc)
        return dt.astimezone(ZoneInfo("America/Sao_Paulo")).isoformat()


class ItemInDbListBaseCielo(BaseModel):
    serial: str
    status: ItemStatus = Field(
        ...,
        description=f"Status atual do item. Opções: {[e.value for e in ItemStatus]}",
        example=ItemStatus.IN_DEPOT
    )
    location_name: str
    location_deps: Optional[str] = None
    product_sku: str
    product_description: str
    produtct_category: str
    last_movement_in_date: Optional[datetime.datetime] = None
    stock_type: Optional[str] = None
    extra_consulta_sincrona_matnr: Optional[str] = None
    extra_consulta_sincrona_sernr: Optional[str] = None
    extra_consulta_sincrona_ztipo: Optional[str] = None
    # extra_consulta_sincrona_lager: Optional[str] = None
    # extra_consulta_sincrona_lgort: Optional[str] = None
    extra_consulta_sincrona_equnr: Optional[str] = None
    # extra_consulta_sincrona_sttxt: Optional[str] = None
    # extra_consulta_sincrona_sttxu: Optional[str] = None
    # extra_consulta_sincrona_zsta_eq: Optional[str] = None
    extra_consulta_sincrona_zver_ap: Optional[str] = None

    extra_info: Optional[dict[str, Any]] = None
    id: int

    @field_serializer("last_movement_in_date",  when_used="always")
    def serialize_dt(self, dt: datetime.datetime | None):
        if dt is None:
            return None
        if dt.tzinfo is None:
            # se vier naive, assume que está em UTC
            dt = dt.replace(tzinfo=datetime.timezone.utc)
        return dt.astimezone(ZoneInfo("America/Sao_Paulo")).isoformat()


class ItemPedidoInDbBase(ItemBase):
    id: int
    in_order_number: str


class Item(ItemInDbBase):
    pass


class ItemInRetornoPickingBase(BaseModel):
    serial: str
    status: ItemStatus = Field(
        ...,
        description=f"Status atual do item. Opções: {[e.value for e in ItemStatus]}",
        example=ItemStatus.IN_DEPOT
    )
    product_sku: str
    product_description: str
    produtct_category: str
    chip_serial: Optional[str] = None
    required_chip: Optional[bool] = False
