'''
Renomeie o módulo para config.py
'''
import os
import secrets
from typing import Any, Dict, List, Optional, Union

from pydantic import AnyHttpUrl, validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    SECRET_KEY: str = secrets.token_urlsafe(32)
    DEBUG: bool = True
    DESCRIPTION: str = 'Integração Shipment Order Fulfillment'
    if DEBUG:
        ROOT_PATH: str = '/hg-stock'
        API_V1_STR: str = "/api"
        PROJECT_NAME: str = 'API Estoque - Homologação'
        PSQL_HOST: str = '192.168.0.219'
        WEBHOOK_API_KEY: str = 'homolog4IxlxMgJiC9ALKOFmpB4O344T6b8NgTrO2qaFWKsRGqjT2xEDfVg8Oa1t'
    else:
        ROOT_PATH: str = '/stock'
        API_V1_STR: str = "/api"
        PROJECT_NAME: str = 'API Estoque - Produção'
        PSQL_HOST: str = '192.168.0.220'
        WEBHOOK_API_KEY: str = 'prodMTHK2TVvT5pvA2OBlPsupXppTrcCXaSYBVLkOHcdysP2K5I0ZZKmKMmqDItG621ITm0U4SajCVNrwEyxa3xifS3ML9eL4AiY6YyQLbT2vTR43bguoFV7y4JJZopb'

    # 60 minutes * 24 hours * 8 days = 8 days
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8
    # BACKEND_CORS_ORIGINS is a JSON-formatted list of origins
    # e.g: '["http://localhost", "http://localhost:4200", "http://localhost:3000", \
    # "http://localhost:8080", "http://local.dockertoolbox.tiangolo.com"]'
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = []

    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    PSQL_USER: str = 'sa'
    PSQL_PASSWORD: str = 'Profeta_01'
    PSQL_DATABASE: str = 'arancia_db'
    PSQL_PORT: int = 5432
    SQLALCHEMY_DATABASE_URI_PG: Optional[str] = None

    @validator("SQLALCHEMY_DATABASE_URI_PG", pre=True)
    def assemble_db_connection_psql(cls, v: Optional[str], values: Dict[str, Any]) -> Any:
        if isinstance(v, str):
            return v
        return (
            f'postgresql+asyncpg://{values.get("PSQL_USER")}:'
            f'{values.get("PSQL_PASSWORD")}@{values.get("PSQL_HOST")}:'
            f'{values.get("PSQL_PORT", 5432)}/{values.get("PSQL_DATABASE")}'
        )

    SQL_HOST_ag_ws: str = '192.168.0.211'
    SQL_USER_ag_ws: str = 'fastapi'
    SQL_PASSWORD_ag_ws: str = 'Profeta#2'
    SQL_DATABASE_ag_ws: str = 'agyx_ws'
    SQLALCHEMY_DATABASE_URI_ag_ws: Optional[str] = None

    @validator("SQLALCHEMY_DATABASE_URI_ag_ws", pre=True)
    def assemble_db_connection_212(cls, v: Optional[str], values: Dict[str, Any]) -> Any:
        if isinstance(v, str):
            return v
        return f'mssql+pyodbc://{values.get("SQL_USER_ag_ws")}:{values.get("SQL_PASSWORD_ag_ws")}@{values.get("SQL_HOST_ag_ws")}/{values.get("SQL_DATABASE_ag_ws")}?driver=ODBC+Driver+17+for+SQL+Server'

    SQL_HOST_211: str = '192.168.0.211'
    SQL_USER_211: str = 'fastapi'
    SQL_PASSWORD_211: str = 'Profeta#2'
    SQL_DATABASE_211: str = 'Lyon_SQL'
    SQLALCHEMY_DATABASE_URI_211: Optional[str] = None

    @validator("SQLALCHEMY_DATABASE_URI_211", pre=True)
    def assemble_db_connection_211(cls, v: Optional[str], values: Dict[str, Any]) -> Any:
        if isinstance(v, str):
            return v
        return f'mssql+pyodbc://{values.get("SQL_USER_211")}:{values.get("SQL_PASSWORD_211")}@{values.get("SQL_HOST_211")}/{values.get("SQL_DATABASE_211")}?driver=ODBC+Driver+17+for+SQL+Server'

    class Config:
        case_sensitive = True

    TEMPO_URL: str = 'http://localhost:4317'

    EVENTS_INTELIPOST: dict = {
        '200': 'Recebido para Picking',
        '201': 'PCP',
        '202': 'Retorno do Picking',
        '203': 'Consolidação',
        '204': 'Expedição',
        '205': 'Troca de custódia',
    }


settings = Settings()
