import datetime
from typing import Optional
from zoneinfo import ZoneInfo

from pydantic import BaseModel, Field, ConfigDict, field_serializer


class ProvisionalSerialBase(BaseModel):
    old_serial_number: Optional[str] = Field(
        None, description="Serial antigo (se houver)"
    )
    reason: Optional[str] = Field(
        None, description="Motivo da criação do serial provisório"
    )
    created_by: str = Field(
        ..., description="Usuário responsável pela criação"
    )
    item_id: Optional[int] = Field(
        None, description="ID do item relacionado"
    )


class ProvisionalSerialCreate(ProvisionalSerialBase):
    """
    Schema para criação de serial provisório.
    O new_serial_number é gerado automaticamente.
    """
    pass


class ProvisionalSerialUpdate(BaseModel):

    model_config = ConfigDict(extra="forbid")


class ProvisionalSerialInDbBase(ProvisionalSerialBase):
    id: int
    new_serial_number: str
    created_at: datetime.datetime

    # Se quiser expor o relacionamento
    # item: Optional[ItemResponseSchema] = None

    model_config = ConfigDict(
        from_attributes=True
    )

    @field_serializer("created_at",  when_used="always")
    def serialize_dt(self, dt: datetime.datetime | None):
        if dt is None:
            return None
        if dt.tzinfo is None:
            # se vier naive, assume que está em UTC
            dt = dt.replace(tzinfo=datetime.timezone.utc)
        return dt.astimezone(ZoneInfo("America/Sao_Paulo")).isoformat()
