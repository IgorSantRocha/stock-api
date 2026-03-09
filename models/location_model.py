import enum
from sqlalchemy import (
    Column, Integer, String, DateTime, ForeignKey, JSON, Enum, UniqueConstraint, func
)
from sqlalchemy.orm import relationship
from db.base_class import Base
from sqlalchemy.orm import declarative_base


class AranciaGroup(Base):
    __tablename__ = "auth_group"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)


class Location(Base):
    __tablename__ = "logistica_groupaditionalinformation"

    id = Column(Integer, primary_key=True, index=True)

    # Campos espelhando o Django GroupAditionalInformation
    nome = Column(String(100), nullable=True)
    cod_iata = Column(String(100), nullable=True, index=True)
    sales_channel = Column(String(100), nullable=True, index=True)
    deposito = Column(String(100), nullable=True, index=True)

    logradouro = Column(String(255), nullable=True)
    numero = Column(String(10), nullable=True)
    complemento = Column(String(100), nullable=True)
    bairro = Column(String(100), nullable=True)
    cidade = Column(String(100), nullable=True, index=True)

    # Mantive ambos (como no Django). Se forem redundantes, escolha um só.
    UF = Column(String(2), nullable=True, index=True)
    # estado = Column(String(2), nullable=True, index=True)

    CEP = Column(String(10), nullable=True, index=True)

    telefone1 = Column(String(15), nullable=True)
    telefone2 = Column(String(15), nullable=True)
    # tamanho comum p/ e-mail
    email = Column(String(254), nullable=True, index=True)
    responsavel = Column(String(100), nullable=True)

    group_id = Column(Integer, ForeignKey("auth_group.id"), nullable=True)
    group = relationship(
        "AranciaGroup",
        foreign_keys=[group_id],
        lazy="joined",
    )
