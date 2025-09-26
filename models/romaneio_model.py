from sqlalchemy import (
    Column, Integer, String, DateTime, ForeignKey, func, event
)
from sqlalchemy.orm import relationship
from db.base_class import Base
from sqlalchemy import text


class Romaneio(Base):
    __tablename__ = "logistic_stock_reverse"

    id = Column(Integer, primary_key=True)
    client_id = Column(Integer, ForeignKey(
        "logistic_stock_client.id"))
    romaneio_number = Column(String, unique=True, index=True)

    location_id = Column(Integer, ForeignKey(
        "logistica_groupaditionalinformation.id"))
    status_rom = Column(String, nullable=False, default="ABERTO", index=True)

    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    created_by = Column(String, nullable=False)
    update_at = Column(DateTime, onupdate=func.now())
    update_by = Column(String, nullable=True)

    location = relationship(
        "Location",
        foreign_keys=[location_id],
        lazy="joined",
    )
    client = relationship(
        "Client",
        foreign_keys=[client_id],
        lazy="joined",
    )


@event.listens_for(Romaneio, "before_insert")
def generate_romaneio_number(mapper, connection, target):
    if not target.client_id:
        raise ValueError("client_id deve ser definido antes de salvar.")

    result = connection.execute(
        text(f"SELECT COALESCE(MAX(id), 0) + 1 FROM {Romaneio.__tablename__}")
    )
    next_id = result.scalar()

    target.romaneio_number = f"AR{target.client_id}{str(next_id).zfill(8)}"
