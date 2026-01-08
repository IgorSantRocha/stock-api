import enum
from typing import List, Optional, Any, Dict
import datetime
from zoneinfo import ZoneInfo
from pydantic import BaseModel, Field, field_serializer
from schemas.item_schema import ItemPayload
from schemas.product_schema import ProductCreate


class MovementType(enum.Enum):
    IN = "IN"
    DELIVERY = "DELIVERY"  # entrega
    RETURN = "RETURN"  # reversa
    TRANSFER = "TRANSFER"
    ADJUST = "ADJUST"
    ERROR = "ERROR"
    COLLECTED = "COLLECTED"


class MovementPayload(BaseModel):
    item: ItemPayload
    client_name: str
    movement_type: MovementType = Field(
        ...,
        description="Tipo da movimentação (IN, OUT, TRANSFER, ADJUST, RETURN, PICK, PACK)",
        example="IN"
    )

    from_location_id: Optional[int] = Field(
        None,
        description="ID da localização de origem (FK para logistica_groupaditionalinformation)",
        example=1
    )
    to_location_id: Optional[int] = Field(
        None,
        description="ID da localização de destino (FK para logistica_groupaditionalinformation)",
        example=2
    )

    order_origin_id: Optional[int] = Field(
        None,
        description="ID da origem do pedido (FK para logistic_stock_origin)",
        example=3
    )
    order_number: Optional[str] = Field(
        None,
        description="Número da ordem associada à movimentação",
        example="ORD2025000123"
    )
    volume_number: Optional[int] = Field(
        default=None,
        ge=0,
        description="Número do volume associado à movimentação (se aplicável)",
        example=10
    )
    kit_number: Optional[str] = Field(
        None,
        description="Identificador do kit associado à movimentação",
        example="KIT-789"
    )
    created_by: Optional[str] = Field(
        None,
        description="Usuário ou sistema responsável pela criação do registro",
        example="ARC0001"
    )
    extra_info: Optional[Dict[str, Any]] = Field(
        None,
        description="Metadados extras da movimentação em formato JSON",
        example={"original_code": "209",
                 "original_message": "VOLUME RECEBIDO PARA CONFERENCIA"}
    )


class MovementPayloadListItem(MovementPayload):
    item: List[ItemPayload]


class MovementBase(BaseModel):
    movement_type: MovementType = Field(
        ...,
        description="Tipo da movimentação (IN, OUT, TRANSFER, ADJUST, RETURN, PICK, PACK)",
        example="IN"
    )
    item_id: int = Field(
        ...,
        description="ID do item movimentado (FK para logistic_stock_item)",
        example=101
    )

    from_location_id: Optional[int] = Field(
        None,
        description="ID da localização de origem (FK para logistica_groupaditionalinformation)",
        example=1
    )
    to_location_id: Optional[int] = Field(
        None,
        description="ID da localização de destino (FK para logistica_groupaditionalinformation)",
        example=2
    )

    order_origin_id: Optional[int] = Field(
        None,
        description="ID da origem do pedido (FK para logistic_stock_origin)",
        example=3
    )
    order_number: Optional[str] = Field(
        None,
        description="Número da ordem associada à movimentação",
        example="ORD-2025-000123"
    )
    volume_number: Optional[int] = Field(
        default=None,
        ge=0,
        description="Número do volume associado à movimentação (se aplicável)",
        example=10
    )
    kit_number: Optional[str] = Field(
        None,
        description="Identificador do kit associado à movimentação",
        example="KIT-789"
    )

    extra_info: Optional[Dict[str, Any]] = Field(
        None,
        description="Metadados extras da movimentação em formato JSON",
        example={"reason": "ajuste inventário", "user": "rafael"}
    )
    created_by: Optional[str] = Field(
        None,
        description="Usuário ou sistema responsável pela criação do registro",
        example="sistema_importacao"
    )

    # Pydantic v2
    model_config = {"from_attributes": True, "use_enum_values": True}
    # v1:
    # class Config:
    #     orm_mode = True
    #     use_enum_values = True


class MovementCreate(MovementBase):
    """Schema usado para criar uma nova movimentação"""
    pass


class MovementUpdate(MovementBase):
    """Schema usado para atualizar uma movimentação existente"""
    pass  # se quiser PATCH estrito, torne todos os campos opcionais aqui


class MovementInDbBase(MovementBase):
    id: int = Field(..., description="ID interno da movimentação",
                    example=5001)
    created_at: datetime.datetime = Field(
        ...,
        description="Data/hora em que a movimentação foi registrada",
        example="2025-08-30T10:15:00"
    )

    @field_serializer("created_at",  when_used="always")
    def serialize_dt(self, dt: datetime.datetime | None):
        if dt is None:
            return None
        if dt.tzinfo is None:
            # se vier naive, assume que está em UTC
            dt = dt.replace(tzinfo=datetime.timezone.utc)
        return dt.astimezone(ZoneInfo("America/Sao_Paulo")).isoformat()


class Movement(MovementInDbBase):
    """Schema retornado pela API ao consultar uma movimentação"""
    pass
