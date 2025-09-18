import datetime
from typing import Optional
from pydantic import BaseModel


class RomaneioItemPayload(BaseModel):
    serial: str
    volume_number: str
    kit_number: str
    client: str
    location_id: int


class RomaneioItemBase(BaseModel):
    romaneio_id: Optional[int] = None
    item_id: Optional[int] = None
    volume_number: str
    kit_number: Optional[str] = None
    created_by: str


class RomaneioItemCreate(RomaneioItemBase):
    pass


class RomaneioItemUpdate(BaseModel):
    romaneio_id: Optional[int] = None
    item_id: Optional[int] = None
    volume_number: Optional[str] = None
    kit_number: Optional[str] = None
    created_by: Optional[str] = None


class RomaneioItemInDbBase(RomaneioItemBase):
    id: int
    created_at: datetime.datetime

    class Config:
        from_attributes = True  # permite usar .from_orm()


class RomaneioItem(RomaneioItemInDbBase):
    pass
