import datetime
from typing import Optional
from pydantic import BaseModel


# Se já tiver o Enum no seu módulo de modelos, importe-o:
# from .models import RomaneioType


class RomaneioBase(BaseModel):
    status_rom: str
    item_id: int
    volume_number: int
    kit_number: int

    created_at: datetime.datetime
    created_by: str
    update_at: Optional[datetime.datetime] = None
    update_by: Optional[str] = None


class RomaneioCreate(RomaneioBase):
    pass


class RomaneioUpdate(RomaneioBase):
    pass  # se quiser "PATCH estrito", mantenha todos opcionais aqui


class RomaneioInDbBase(RomaneioBase):
    id: int


class Romaneio(RomaneioInDbBase):
    pass
