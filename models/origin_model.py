from datetime import datetime, timezone
from sqlalchemy import (
    Column, DateTime, ForeignKey, Integer, String, UniqueConstraint, Index, func
)
from db.base_class import Base
from sqlalchemy.orm import relationship
from sqlalchemy.ext.hybrid import hybrid_property


class OrderOrigin(Base):
    __tablename__ = "logistic_stock_order_origin"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),  # ✅ Python
        server_default=func.now(),
        nullable=False
    )

    # Cliente final (Cielo, Claro, etc. — se quiser separar de origin_name)
    # client_name = Column(String(100), nullable=True, index=True)
    @hybrid_property
    def client_name(self):
        return self.client.client_code if self.client else None

    client_id = Column(Integer, ForeignKey(
        "logistic_stock_client.id"))
    # Projeto - de onde veio o pedido (ex.: "LastMile (B2C)")
    project_name = Column(String(100), nullable=True, index=True)

    # Sistema/forma de envio da OS - Ex.: "SAP", "SALES_FORCE", "GTEC", etc.
    origin_name = Column(String(100), nullable=False, index=True)

    stock_type = Column(String(50), nullable=True)

    client = relationship(
        "Client",
        foreign_keys=[client_id],
        lazy="joined",
    )
    __table_args__ = (
        UniqueConstraint(
            "origin_name", "project_name", "client_id", "stock_type",
            name="uq_origin_business_key"
        ),
        Index("ix_origin_name_project", "origin_name",
              "project_name", "stock_type"),
    )

    def __repr__(self) -> str:
        return f"<OrderOrigin {self.origin_name}/{self.project_name or '-'}@{self.client_name or '-'}>"
