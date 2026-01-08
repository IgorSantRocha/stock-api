import enum
from sqlalchemy import (
    Column, Integer, String, DateTime, ForeignKey, JSON, Enum, UniqueConstraint, func, event, text
)
from sqlalchemy.orm import relationship
from db.base_class import Base
from sqlalchemy.orm import declarative_base
from sqlalchemy.ext.hybrid import hybrid_property
from datetime import datetime


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
    # Conta quantos registros já existem HOJE
    result = connection.execute(
        text(
            f"""
            SELECT COUNT(*) 
            FROM {ProvisionalSerialItem.__tablename__}
            WHERE created_at::date = CURRENT_DATE
            """
        )
    )

    daily_count = result.scalar() or 0
    next_sequence = daily_count + 1

    # Data atual
    now = datetime.now()
    year = str(now.year)[-2:]
    month = str(now.month).zfill(2)
    day = str(now.day).zfill(2)

    # ILG-DDMMYY-0001
    target.new_serial_number = (
        f"ILG-{day}{month}{year}-{str(next_sequence).zfill(4)}"
    )
