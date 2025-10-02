import datetime
from typing import Optional
from zoneinfo import ZoneInfo
from pydantic import BaseModel, field_serializer


class RomaneioBase(BaseModel):
    status_rom: Optional[str] = "ABERTO"  # default igual ao model
    created_by: str
    update_by: Optional[str] = None
    client_id: int


class RomaneioCreate(BaseModel):
    created_by: str
    location_id: int
    client_id: int
    # Se no create você quiser deixar o status fixo como default (sem aceitar override),
    # pode até remover `status_rom` daqui.


class RomaneioCreateV2(BaseModel):
    created_by: str
    location_id: int
    client_name: str
    # Se no create você quiser deixar o status fixo como default (sem aceitar override),
    # pode até remover `status_rom` daqui.


class RomaneioUpdate(BaseModel):
    # No update geralmente todos os campos são opcionais (PATCH style)
    status_rom: Optional[str] = None
    update_by: Optional[str] = None


class RomaneioInDbBase(RomaneioBase):
    id: int
    created_at: datetime.datetime
    update_at: Optional[datetime.datetime] = None
    romaneio_number: str
    location_id: int

    @field_serializer("created_at", "update_at", when_used="always")
    def serialize_dt(self, dt: datetime.datetime | None):
        if dt is None:
            return None
        if dt.tzinfo is None:
            # se vier naive, assume que está em UTC
            dt = dt.replace(tzinfo=datetime.timezone.utc)
        return dt.astimezone(ZoneInfo("America/Sao_Paulo")).isoformat()

    class Config:
        from_attributes = True  # importante p/ SQLAlchemy -> Pydantic


class Romaneio(RomaneioInDbBase):
    pass
