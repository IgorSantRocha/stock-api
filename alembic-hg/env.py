# env.py
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context

from core.config import settings

# Importa o Base e, MUITO IMPORTANTE, registra todos os modelos no metadata:
from db.base_class import Base
import db.base  # <- garante que todas as tabelas sejam anexadas ao Base.metadata
from models import *  # noqa: F403,F401

# Alembic config
config = context.config
# injeta a URL (ou deixe no .ini e remova esta linha)
config.set_main_option(
    'sqlalchemy.url', 'postgresql://sa:Profeta_01@192.168.0.219:5432/arancia_db')

# Logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Metadata para autogenerate
target_metadata = Base.metadata

# ========= CUSTOM =========
# version table exclusiva deste projeto
VERSION_TABLE = "alembic_version_stock"
PREFIX = "logistic_stock_"               # >>> AJUSTE AQUI para o prefixo real


def include_name(name: str | None, type_: str, parent_names: dict) -> bool:
    """
    Inclui somente objetos pertencentes a tabelas com o PREFIX.
    """
    if not name and not parent_names:
        return True

    if type_ == "table":
        return bool(name and name.startswith(PREFIX))

    table = parent_names.get("table_name")
    if table:
        return table.startswith(PREFIX)

    return True
# ==========================


def _get_url() -> str:
    url = config.get_main_option("sqlalchemy.url")
    return url or 'postgresql://sa:Profeta_01@192.168.0.219:5432/arancia_db'


def run_migrations_offline() -> None:
    url = _get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_name=include_name,
        compare_type=True,
        compare_server_default=True,
        version_table=VERSION_TABLE,
        # Se você usa schemas além do "public", ative:
        # include_schemas=True,
        # version_table_schema="public",
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    section = config.get_section(config.config_ini_section, {})
    section.setdefault("sqlalchemy.url", _get_url())

    connectable = engine_from_config(
        section,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            include_name=include_name,
            compare_type=True,
            compare_server_default=True,
            version_table=VERSION_TABLE,
            # include_schemas=True,
            # version_table_schema="public",
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
