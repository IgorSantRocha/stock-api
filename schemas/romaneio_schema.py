import datetime
from typing import Optional
from pydantic import BaseModel


class RomaneioBase(BaseModel):
    status_rom: Optional[str] = "ABERTO"  # default igual ao model
    created_by: str
    update_by: Optional[str] = None


class RomaneioCreate(RomaneioBase):
    pass
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
    reverse_item_name: str

    class Config:
        from_attributes = True  # importante p/ SQLAlchemy -> Pydantic


class Romaneio(RomaneioInDbBase):
    pass
