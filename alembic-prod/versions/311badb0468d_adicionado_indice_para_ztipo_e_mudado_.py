"""Adicionado indice para Ztipo e mudado tipo da coluna extra

Revision ID: 311badb0468d
Revises: 60d70b20d175
Create Date: 2026-01-06 22:53:55.748300

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '311badb0468d'
down_revision: Union[str, Sequence[str], None] = '60d70b20d175'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # ============================
    # 1. Converter extra_info JSON -> JSONB
    # ============================
    op.execute(
        """
        ALTER TABLE logistic_stock_item
        ALTER COLUMN extra_info
        TYPE JSONB
        USING extra_info::jsonb
        """
    )

    # ============================
    # 2. Criar índice funcional + parcial (ZTIPO)
    # ============================
    op.create_index(
        "ix_item_extra_ztipo",
        "logistic_stock_item",
        [sa.text("(extra_info -> 'consulta_sincrona' ->> 'ZTIPO')")],
        postgresql_where=sa.text(
            "(extra_info -> 'consulta_sincrona' ->> 'ZTIPO') IS NOT NULL"
        ),
    )


def downgrade():
    # ============================
    # 1. Remover índice ZTIPO
    # ============================
    op.drop_index(
        "ix_item_extra_ztipo",
        table_name="logistic_stock_item"
    )

    # ============================
    # 2. Converter JSONB -> JSON
    # ============================
    op.execute(
        """
        ALTER TABLE logistic_stock_item
        ALTER COLUMN extra_info
        TYPE JSON
        USING extra_info::json
        """
    )
