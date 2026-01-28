import datetime
from typing import List, Optional
from zoneinfo import ZoneInfo
from pydantic import BaseModel, field_serializer
from schemas.product_schema import ProductInDbBase


class RomaneioItemKit(BaseModel):
    id: int
    kit_number: str
    serial: str
    order_number: str
    created_by: str
    created_at: datetime.datetime
    product_data: Optional[ProductInDbBase] = None

    @field_serializer("created_at", when_used="always")
    def serialize_dt(self, dt: datetime.datetime | None):
        if dt is None:
            return None
        if dt.tzinfo is None:
            # se vier naive, assume que está em UTC
            dt = dt.replace(tzinfo=datetime.timezone.utc)
        return dt.astimezone(ZoneInfo("America/Sao_Paulo")).isoformat()


class RomaneioItemVolum(BaseModel):
    volum_number: str
    kits: List[RomaneioItemKit]


class RomaneioItemResponse(BaseModel):
    romaneio: str
    status: str
    location_id: int
    location: Optional[str] = None
    origin_id: Optional[int] = None
    origin: Optional[str] = None
    destination_id: Optional[int] = None
    destination: Optional[str] = None
    volums: List[RomaneioItemVolum]


class RomaneioItemPayload(BaseModel):
    serial: str
    volume_number: str
    kit_number: str
    client: str
    location_id: int
    create_by: str


class RomaneioItemBase(BaseModel):
    romaneio_id: Optional[int] = None
    item_id: Optional[int] = None
    volume_number: str
    kit_number: Optional[str] = None
    created_by: str


class RomaneioItemCreate(RomaneioItemBase):
    order_number: str


class RomaneioItemUpdateKit(BaseModel):
    kit_number: Optional[str] = None


class RomaneioItemUpdate(BaseModel):
    romaneio_id: Optional[int] = None
    item_id: Optional[int] = None
    volume_number: Optional[str] = None
    kit_number: Optional[str] = None
    created_by: Optional[str] = None


class RomaneioItemInDbBase(RomaneioItemBase):
    id: int
    created_at: datetime.datetime
    order_number: str
    status: str

    @field_serializer("created_at", when_used="always")
    def serialize_dt(self, dt: datetime.datetime | None):
        if dt is None:
            return None
        if dt.tzinfo is None:
            # se vier naive, assume que está em UTC
            dt = dt.replace(tzinfo=datetime.timezone.utc)
        return dt.astimezone(ZoneInfo("America/Sao_Paulo")).isoformat()

    class Config:
        from_attributes = True  # permite usar .from_orm()


class RomaneioItem(RomaneioItemInDbBase):
    pass
