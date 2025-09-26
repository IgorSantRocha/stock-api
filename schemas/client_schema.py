from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel


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
    created_at: datetime

    class Config:
        from_attributes = True  # pydantic v2 (equivalente ao orm_mode=True)


# Retornos
class ClientInDBSC(ClientInDBBaseSC):
    pass


class ClientOutSC(ClientInDBBaseSC):
    pass
