from datetime import datetime, timezone
import enum
from sqlalchemy import (
    Column, Integer, String, DateTime, ForeignKey, JSON, Enum, UniqueConstraint, func
)
from sqlalchemy.orm import relationship
from db.base_class import Base
from sqlalchemy.orm import declarative_base


class RomaneioItem(Base):
    __tablename__ = "logistic_stock_reverse_item"
    id = Column(Integer, primary_key=True)
    romaneio_id = Column(Integer, ForeignKey(
        "logistic_stock_reverse.id"), nullable=True, index=True)

    item_id = Column(Integer, ForeignKey(
        "logistic_stock_item.id"), nullable=True, index=True)
    volume_number = Column(String, nullable=False)
    kit_number = Column(String, nullable=True)

    order_number = Column(String, nullable=False)

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),  # ✅ Python
        server_default=func.now(),
        nullable=False
    )
    created_by = Column(String, nullable=False)

    item = relationship("Item", foreign_keys=[item_id], lazy="selectin")
    romaneio = relationship("Romaneio", lazy="selectin")
