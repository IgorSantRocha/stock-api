from datetime import datetime
from typing import Optional
from schemas.base import BaseSchema
from pydantic import BaseModel, Field, ConfigDict


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


class ProvisionalSerialUpdate(ProvisionalSerialBase):

    model_config = ConfigDict(extra="forbid")


class ProvisionalSerialInDbBase(ProvisionalSerialBase):
    id: int
    new_serial_number: str
    created_at: datetime

    # Se quiser expor o relacionamento
    # item: Optional[ItemResponseSchema] = None

    model_config = ConfigDict(
        from_attributes=True
    )
