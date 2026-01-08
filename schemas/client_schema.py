import datetime
from typing import Optional, Dict, Any
from zoneinfo import ZoneInfo
from pydantic import BaseModel, field_serializer


# Base: campos que podem ser reaproveitados
class ClientBaseSC(BaseModel):
    client_code: str
    client_name: Optional[str] = None
    created_by: Optional[str] = None
    extra_info: Optional[Dict[str, Any]] = None


# Schema para criação (obrigatório client_code)
class ClientCreateSC(ClientBaseSC):
    client_code: str


# Schema para update (todos opcionais)
class ClientUpdateSC(BaseModel):
    client_code: Optional[str] = None
    client_name: Optional[str] = None
    created_by: Optional[str] = None
    extra_info: Optional[Dict[str, Any]] = None


# Schema principal (retorno)
class ClientInDBBaseSC(ClientBaseSC):
    id: int
    created_at: datetime.datetime

    @field_serializer("created_at",  when_used="always")
    def serialize_dt(self, dt: datetime.datetime | None):
        if dt is None:
            return None
        if dt.tzinfo is None:
            # se vier naive, assume que está em UTC
            dt = dt.replace(tzinfo=datetime.timezone.utc)
        return dt.astimezone(ZoneInfo("America/Sao_Paulo")).isoformat()

    class Config:
        from_attributes = True  # pydantic v2 (equivalente ao orm_mode=True)


# Retornos
class ClientInDBSC(ClientInDBBaseSC):
    pass


class ClientOutSC(ClientInDBBaseSC):
    pass
