import enum
from sqlalchemy import (
    Column, Integer, String, DateTime, ForeignKey, JSON, Enum, UniqueConstraint, func
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from db.base_class import Base
from sqlalchemy.orm import declarative_base
from sqlalchemy import Index, text


class Item(Base):
    __tablename__ = "logistic_stock_item"

    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    product_id = Column(Integer, ForeignKey(
        "logistic_stock_product.id"), nullable=True, index=True)

    serial = Column(String, unique=True, index=True, nullable=True)
    status = Column(String, nullable=False, index=True)

    location_id = Column(Integer, ForeignKey(
        "logistica_groupaditionalinformation.id"), nullable=False, index=True)

    last_in_movement_id = Column(Integer, ForeignKey(
        "logistic_stock_movement.id"), nullable=True)
    last_out_movement_id = Column(Integer, ForeignKey(
        "logistic_stock_movement.id"), nullable=True)

    extra_info = Column(JSONB)

    last_in_movement = relationship(
        "Movement", foreign_keys=[last_in_movement_id], lazy="selectin")
    last_out_movement = relationship(
        "Movement", foreign_keys=[last_out_movement_id], lazy="selectin")

    product = relationship("Product", lazy="selectin")
    location = relationship("Location", lazy="selectin")

    __table_args__ = (
        # Índice funcional + parcial para ZTIPO
        Index(
            "ix_item_extra_ztipo",
            text("(extra_info -> 'consulta_sincrona' ->> 'ZTIPO')"),
            postgresql_where=text(
                "(extra_info -> 'consulta_sincrona' ->> 'ZTIPO') IS NOT NULL"
            ),
        ),
    )
