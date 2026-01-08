import enum
from sqlalchemy import (
    Column, Integer, String, DateTime, ForeignKey, JSON, Enum, UniqueConstraint, func, event, text
)
from sqlalchemy.orm import relationship
from db.base_class import Base
from sqlalchemy.orm import declarative_base
from sqlalchemy.ext.hybrid import hybrid_property


class ProvisionalSerialItem(Base):
    __tablename__ = "logistic_stock_item_provisional_serial"
    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    new_serial_number = Column(String, nullable=False, index=True)
    old_serial_number = Column(String, nullable=True, index=True)

    reason = Column(String, nullable=True)
    created_by = Column(String, nullable=False)

    item_id = Column(Integer, ForeignKey(
        "logistic_stock_item.id"), nullable=True, index=True)

    item = relationship("Item", foreign_keys=[item_id], lazy="selectin")

    __table_args__ = (
        UniqueConstraint(
            'new_serial_number',
            name='uix_logistic_stock_item_provisional_serial_new_serial_number'
        ),
    )


@event.listens_for(ProvisionalSerialItem, "before_insert")
def generate_romaneio_number(mapper, connection, target):
    result = connection.execute(
        text(
            f"SELECT COALESCE(MAX(id), 0) + 1 FROM {ProvisionalSerialItem.__tablename__}")
    )
    next_id = result.scalar()

    # monta o ano com 2 dígitos
    year = str(func.now().year)[-2:]
    month = str(func.now().month).zfill(2)
    day = str(func.now().day).zfill(2)

    # padrão esperado para new_serial_number: ILG-010126-9926"
    target.new_serial_number = f"ILG-{day}{month}{year}-{str(next_id).zfill(4)}"
