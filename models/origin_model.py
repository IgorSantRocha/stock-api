from sqlalchemy import Column, Integer, String, UniqueConstraint, Index
from db.base_class import Base


class Origin(Base):
    __tablename__ = "logistic_stock_origin"

    id = Column(Integer, primary_key=True, index=True)
    origin_name = Column(String(100), nullable=False)
    project_name = Column(String(100), nullable=True)
    client_name = Column(String(100), nullable=True)

    __table_args__ = (
        UniqueConstraint("origin_name", "project_name",
                         "client_name", name="uq_origin_triplet"),
        Index("ix_origin_origin_name", "origin_name"),
        Index("ix_origin_client_name", "client_name"),
    )

    def __repr__(self) -> str:
        return f"< Origin {self.origin_name} | {self.project} | {self.client_name} >"
