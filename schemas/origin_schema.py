from typing import Optional
from pydantic import BaseModel, Field


class OrderOriginBase(BaseModel):
    origin_name: str = Field(
        ...,
        description="Nome da origem do pedido (ex.: sistema ou integração de onde veio a ordem)",
        example="CIELO"
    )
    project_name: Optional[str] = Field(
        None,
        description="Nome do projeto ou sistema interno relacionado à origem",
        example="LastMile (B2C)"
    )
    client_name: Optional[str] = Field(
        None,
        description="Nome do cliente associado à origem",
        example="C-Trends"
    )

    model_config = {
        "from_attributes": True,
        "populate_by_name": True  # permite aceitar tanto 'origin_name' quanto 'nome_origem'
    }


class OrderOriginCreate(OrderOriginBase):
    """Schema usado na criação de uma origem de pedidos"""
    pass


class OrderOriginUpdate(OrderOriginBase):
    """Schema usado na atualização de uma origem de pedidos"""
    pass


class OrderOriginInDbBase(OrderOriginBase):
    id: int = Field(...,
                    description="ID interno da origem no banco de dados", example=1)


class OrderOrigin(OrderOriginInDbBase):
    """Schema retornado pela API ao consultar uma origem"""
    pass
