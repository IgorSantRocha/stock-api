import datetime
from typing import List, Optional
from pydantic import BaseModel


class RomaneioItemKit(BaseModel):
    kit_number: str
    serial: str
    order_number: str
    created_by: str
    created_at: datetime.datetime


class RomaneioItemVolum(BaseModel):
    volum_number: str
    kits: List[RomaneioItemKit]


class RomaneioItemResponse(BaseModel):
    romaneio: str
    status: str
    location_id: Optional[int] = None
    volums: List[RomaneioItemVolum]

    def __init__(self, **data):
        super().__init__(**data)
        self.romaneio = f"AR{str(self.romaneio).zfill(5)}"


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

    class Config:
        from_attributes = True  # permite usar .from_orm()


class RomaneioItem(RomaneioItemInDbBase):
    pass
