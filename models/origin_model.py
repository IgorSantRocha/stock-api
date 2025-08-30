from sqlalchemy import (
    Column, DateTime, Integer, String, UniqueConstraint, Index, func
)
from db.base_class import Base


class OrderOrigin(Base):
    __tablename__ = "logistic_stock_order_origin"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    # Cliente final (Cielo, Claro, etc. — se quiser separar de origin_name)
    client_name = Column(String(100), nullable=True, index=True)
    # Projeto - de onde veio o pedido (ex.: "LastMile (B2C)")
    project_name = Column(String(100), nullable=True, index=True)

    # Sistema/forma de envio da OS - Ex.: "SAP", "SALES_FORCE", "GTEC", etc.
    origin_name = Column(String(100), nullable=False, index=True)

    __table_args__ = (
        UniqueConstraint(
            "origin_name", "project_name", "client_name",
            name="uq_origin_business_key"
        ),
        Index("ix_origin_name_project", "origin_name", "project_name"),
    )

    def __repr__(self) -> str:
        return f"<OrderOrigin {self.origin_name}/{self.project_name or '-'}@{self.client_name or '-'}>"
