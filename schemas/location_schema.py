from typing import Optional
from pydantic import BaseModel


# Se já tiver o Enum no seu módulo de modelos, importe-o:
# from .models import LocationType


class LocationBase(BaseModel):
    nome: Optional[str] = None
    cod_iata: Optional[str] = None
    sales_channel: Optional[str] = None
    deposito: Optional[str] = None

    logradouro: Optional[str] = None
    numero: Optional[str] = None
    complemento: Optional[str] = None
    bairro: Optional[str] = None
    cidade: Optional[str] = None

    UF: Optional[str] = None
    estado: Optional[str] = None
    CEP: Optional[str] = None

    telefone1: Optional[str] = None
    telefone2: Optional[str] = None
    email: Optional[str] = None
    responsavel: Optional[str] = None

    # Pydantic v2
    model_config = {"from_attributes": True, "use_enum_values": True}
    # Se estiver em Pydantic v1, use:
    # class Config:
    #     orm_mode = True
    #     use_enum_values = True


class LocationCreate(LocationBase):
    pass


class LocationUpdate(LocationBase):
    pass  # se quiser "PATCH estrito", mantenha todos opcionais aqui


class LocationInDbBase(LocationBase):
    id: int


class Location(LocationInDbBase):
    pass
