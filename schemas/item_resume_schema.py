from pydantic import BaseModel, Field
from typing import Dict, List, Optional
from schemas.base import BaseSchema


class StockTypeResumeSchema(BaseModel):
    type: str = Field(
        ...,
        description="Tipo de estoque (ex: Aguardando Reversa, Suprimento P/ Entrega)"
    )
    total: int = Field(
        ...,
        description="Total de itens nesse tipo de estoque"
    )
    qtd_por_produto: Dict[str, int] = Field(
        default_factory=dict,
        description="Quantidade de itens agrupados por SKU do produto"
    )
    qtd_por_ztipo: Dict[str, int] = Field(
        default_factory=dict,
        description="Quantidade de itens agrupados por ZTIPO (extra_info.consulta_sincrona.ZTIPO)"
    )


class PaStockResumeSchema(BaseModel):
    pa: Optional[str] = Field(
        default='Não definida',
        description="Código da PA (ex: SPO, RIO, BSB)"
    )
    stock_types: List[StockTypeResumeSchema] = Field(
        ...,
        description="Lista de tipos de estoque com seus respectivos totais"
    )
