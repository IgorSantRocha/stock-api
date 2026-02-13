from datetime import datetime, timezone
from sqlalchemy import (
    Column, Integer, String, DateTime, ForeignKey, JSON, Enum, func
)
from sqlalchemy.orm import relationship
import enum
from db.base_class import Base


class Movement(Base):
    __tablename__ = "logistic_stock_movement"

    id = Column(Integer, primary_key=True)
    movement_type = Column(String, nullable=False, index=True)

    item_id = Column(Integer, ForeignKey("logistic_stock_item.id"),
                     nullable=False, index=True)

    # NOVO: FK para origem normalizada
    order_origin_id = Column(Integer, ForeignKey(
        "logistic_stock_order_origin.id"), nullable=True, index=True)

    from_location_id = Column(Integer, ForeignKey(
        "logistica_groupaditionalinformation.id"))
    to_location_id = Column(Integer, ForeignKey(
        "logistica_groupaditionalinformation.id"))

    order_number = Column(String, index=True)
    volume_number = Column(Integer)
    kit_number = Column(String, index=True)

    extra_info = Column(JSON)

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),  # ✅ Python
        server_default=func.now(),
        nullable=False
    )
    created_by = Column(String)

    # Relacionamentos
    item = relationship("Item",
                        foreign_keys=[item_id],
                        lazy="joined",)

    origin = relationship("OrderOrigin", lazy="joined")

    from_location = relationship(
        "Location",
        foreign_keys=[from_location_id],
        lazy="joined",
    )
    to_location = relationship(
        "Location",
        foreign_keys=[to_location_id],
        lazy="joined",
    )

    # (Opcional) compat: expor o nome da origem como propriedade
    @property
    def order_origin(self) -> str | None:
        return self.origin.origin_name if self.origin else None
