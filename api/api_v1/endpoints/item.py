from datetime import datetime
from io import BytesIO
from typing import Any, List, Annotated, Literal
import logging
from collections import defaultdict
from fastapi import APIRouter, Depends, HTTPException, status, Query
import fastapi
from fastapi.responses import StreamingResponse
import pandas as pd
from sqlalchemy.orm import Session
from schemas.consulta_sincrona_schema import ResponseConsultaSincSC
from services.consulta_sincrona import ConsultaSincrona
from utils import flatten_dict
from crud.crud_movement import movement
from crud.crud_item import item
from schemas.item_resume_schema import PaStockResumeSchema, ResumeExportSchema

from schemas.item_schema import ItemCreate, ItemInDbListBase, ItemInRetornoPickingBase, ItemProductUpdate, ItemUpdate, ItemInDbBase, ItemPedidoInDbBase, ItemInDbListBaseCielo


from api import deps

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get(
    "/list-byid/{client}/resume",
    response_model=List[PaStockResumeSchema],
    summary="Resumo agregado de estoque por PA"
)
async def read_items_by_client_resume(
    client: str,
    status: str,
    db: Session = Depends(deps.get_db_psql),
    stock_type: str | None = None,
    locations_ids: Annotated[
        list[int] | None,
        Query(description="IDs das locations (pode repetir parâmetro)")
    ] = None,
) -> Any:
    """
Retorna um resumo agregado dos itens de estoque agrupados por:

- PA (location.cod_iata)
- Tipo de estoque
- Produto (SKU)
- ZTIPO (extra_info.consulta_sincrona)

Ideal para dashboards e relatórios.
"""

    logger.info("Consultando resumo agregado de items por client...")

    # ============================
    # FILTERS (iguais ao endpoint original)
    # ============================
    filters = [
        {"field": "status", "operator": "=", "value": status},
        {"field": "product.client.client_code", "operator": "=", "value": client},
    ]

    if locations_ids:
        filters.append({
            "field": "location.id",
            "operator": "in",
            "value": locations_ids
        })

    if stock_type:
        filters.append({
            "field": "last_in_movement.origin.stock_type",
            "operator": "=",
            "value": stock_type
        })

    # ============================
    # 1️ TOTAL POR PA + STOCK TYPE
    # ============================
    totais = await item.get_aggregates(
        db=db,
        filters=filters,
        aggregations=[
            {"op": "count", "field": "id", "alias": "total"}
        ],
        group_by=[
            "location.cod_iata",
            "location.nome",
            "last_in_movement.origin.stock_type"

        ]
    )

    # ============================
    # 2️ QTD POR PRODUTO
    # ============================
    por_produto = await item.get_aggregates(
        db=db,
        filters=filters,
        aggregations=[
            {"op": "count", "field": "id", "alias": "qtd"}
        ],
        group_by=[
            "location.cod_iata",
            "location.nome",
            "last_in_movement.origin.stock_type",
            "product.sku",
            "product.description"
        ]
    )

    # ============================
    # 3️ QTD POR ZTIPO (JSONB)
    # ============================
    por_ztipo = await item.get_aggregates(
        db=db,
        filters=filters,
        aggregations=[
            {"op": "count", "field": "id", "alias": "qtd"}
        ],
        group_by=[
            "location.cod_iata",
            "location.nome",
            "last_in_movement.origin.stock_type",
            "extra_info.consulta_sincrona.ZTIPO",
            "product.description"
        ]
    )

    # ============================
    # 4️ MONTAGEM DO PAYLOAD FINAL
    # ============================
    result: dict = defaultdict(dict)

    # ---- totais
    for row in totais:
        nome_pa = F'{row.get("nome") or "N/A"} ({row["cod_iata"] or "N/A"})'
        pa = nome_pa
        st = row["stock_type"]

        result[pa][st] = {
            "type": st,
            "total": row["total"],
            "qtd_por_produto": {},
            "qtd_por_ztipo": {}
        }

    # ---- produtos
    for row in por_produto:
        nome_pa = F'{row.get("nome") or "N/A"} ({row["cod_iata"] or "N/A"})'
        pa = nome_pa
        st = row["stock_type"]
        sku = row["sku"]
        description = row["description"]
        txt = f"{sku} - {description}"

        if pa in result and st in result[pa]:
            result[pa][st]["qtd_por_produto"][txt] = row["qtd"]

    # ---- ztipo (JSON)
    for row in por_ztipo:
        nome_pa = F'{row.get("nome") or "N/A"} ({row["cod_iata"] or "N/A"})'
        pa = nome_pa
        st = row["stock_type"]
        ztipo = row.get("ZTIPO") or "N/A"
        description = row["description"]
        txt = f"{ztipo} - {description}"

        if pa in result and st in result[pa]:
            result[pa][st]["qtd_por_ztipo"][txt] = row["qtd"]

    # ============================
    # 5️ FORMATA SAÍDA FINAL
    # ============================
    response = []
    for pa, stocks in result.items():
        response.append({
            "pa": pa,
            "stock_types": list(stocks.values())
        })

    return response


@router.get(
    "/list-byid/{client}/resume/export",
    response_model=Any,
    summary="Resumo agregado de estoque por PA"
)
async def read_items_by_client_resume(
    client: str,
    status: str,
    agregate_by: Literal['product', 'ztipo'] = 'product',
    db: Session = Depends(deps.get_db_psql),
    stock_type: str | None = None,
    locations_ids: Annotated[
        list[int] | None,
        Query(description="IDs das locations (pode repetir parâmetro)")
    ] = None,
) -> Any:
    """
Retorna um resumo agregado dos itens de estoque agrupados por:

- PA (location.cod_iata)
- Tipo de estoque
- Produto (SKU)
- ZTIPO (extra_info.consulta_sincrona)

Ideal para dashboards e relatórios.
"""

    if agregate_by == 'ztipo' and client != 'cielo':
        raise HTTPException(
            status_code=fastapi.status.HTTP_400_BAD_REQUEST,
            detail="A agregação por ZTIPO está disponível apenas para o cliente CIELO.",
        )

    arq_name = f'{client}_{status}_itens_by_{agregate_by}'
    logger.info("Consultando resumo agregado de items por client...")

    # ============================
    # FILTERS (iguais ao endpoint original)
    # ============================
    filters = [
        {"field": "status", "operator": "=", "value": status},
        {"field": "product.client.client_code", "operator": "=", "value": client},
    ]

    if locations_ids:
        filters.append({
            "field": "location.id",
            "operator": "in",
            "value": locations_ids
        })
        arq_name += f'_locations_{"_".join(map(str, locations_ids))}'

    if stock_type:
        filters.append({
            "field": "last_in_movement.origin.stock_type",
            "operator": "=",
            "value": stock_type
        })
        arq_name += f'_stocktype_{stock_type}'

    # ============================
    # 21 QTD POR PRODUTO
    # ============================
    por_produto = None
    if agregate_by == 'product':
        por_produto = await item.get_aggregates(
            db=db,
            filters=filters,
            aggregations=[
                {"op": "count", "field": "id", "alias": "qtd"}
            ],
            group_by=[
                "location.cod_iata",
                "location.nome",
                "last_in_movement.origin.stock_type",
                "product.sku",
                "product.description"
            ]
        )

    # ============================
    # 2 QTD POR ZTIPO (JSONB)
    # ============================
    por_ztipo = None
    if agregate_by == 'ztipo':
        por_ztipo = await item.get_aggregates(
            db=db,
            filters=filters,
            aggregations=[
                {"op": "count", "field": "id", "alias": "qtd"}
            ],
            group_by=[
                "location.cod_iata",
                "location.nome",
                "last_in_movement.origin.stock_type",
                "extra_info.consulta_sincrona.ZTIPO",
                "product.description"
            ]
        )

    # ============================
    # 3 MONTAGEM DO PAYLOAD FINAL
    # ============================
    response: list[ResumeExportSchema] = []

    if agregate_by == "product":
        for row in por_produto:
            nome_pa = F'{row.get("nome") or "N/A"} ({row["cod_iata"] or "N/A"})'
            response.append(
                ResumeExportSchema(
                    pa=nome_pa,
                    stock_type=row["stock_type"],
                    product=f'{row["sku"]} - {row["description"]}',
                    qtd=row["qtd"]
                )
            )

    elif agregate_by == "ztipo":
        for row in por_ztipo:
            nome_pa = F'{row.get("nome") or "N/A"} ({row["cod_iata"] or "N/A"})'
            ztipo = row.get("ZTIPO") or "N/A"
            response.append(
                ResumeExportSchema(
                    pa=nome_pa,
                    stock_type=row["stock_type"],
                    product=f'{ztipo} - {row["description"]}',
                    qtd=row["qtd"]
                )
            )

    # === Converter para DataFrame ===
    data = [r.__dict__ for r in response]
    for d in data:
        d.pop('_sa_instance_state', None)

    df = pd.DataFrame(data)
    ordered_columns = list(ResumeExportSchema.__fields__.keys())

    df = df.reindex(columns=ordered_columns)

    for col in df.select_dtypes(include=["datetimetz"]).columns:
        df[col] = df[col].dt.tz_localize(None)

    # === Gerar Excel com formatação ===
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="IN_DEPOT_ITEMS")

    output.seek(0)

    now = datetime.now()
    filename = f"stock{arq_name}_{now.strftime('%d%m%y_%H%M')}.xlsx"

    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/list-byid/{client}", response_model=List[ItemInDbListBase])
async def read_items_by_client(
        client: str,
        status: str,
        db: Session = Depends(deps.get_db_psql),
        stock_type: str = None,
        offset: int = 0,
        limit: int = 100,
        locations_ids: Annotated[
            list[int] | None,
            Query(description="IDs das locations (pode repetir parâmetro)")
        ] = None,
) -> Any:
    """
    # Consulta os items por client e status

    ### Opções de status:
    - `IN_DEPOT` -> Item no depósito
    - `IN_TRANSIT` -> Item em trânsito
    - `WITH_CLIENT` -> Item está em posse do contratante ou um de seus representantes
    - `WITH_CUSTOMER` -> Item está em posse do cliente final (instalado)

    ### Ao usar lista de locations_ids, retorna apenas items que estejam em uma das locations informadas:
    - Exemplo: `?locations_ids=1&locations_ids=2&locations_ids=11`
    """

    logger.info("Consultando products por client...")

    filters = [
        {"field": "status", "operator": "=", "value": status},
        {"field": "product.client.client_code", "operator": "=", "value": client},
    ]

    if locations_ids:
        filters.append({
            "field": "location.id",
            "operator": "in",
            "value": locations_ids  # já vem como lista[int]
        })
    if stock_type:
        filters.append({
            "field": "last_in_movement.origin.stock_type",
            "operator": "=",
            "value": stock_type
        })
    itens = await item.get_multi_filters(
        db=db,
        filters=filters,
        order_by="created_at",
        order_desc=True,
        distinct_on_id=True,  # ativa DISTINCT ON (Item.id)
        offset=offset,
        limit=limit,
    )
    for _item in itens:
        _item.location_name = F'{_item.location.cod_iata}-{_item.location.nome}' if _item.location.cod_iata else _item.location.nome
        _item.product_sku = _item.product.sku
        _item.product_description = _item.product.description
        _item.produtct_category = _item.product.category
        _item.last_movement_in_date = _item.last_in_movement.created_at if _item.last_in_movement else None
        _item.stock_type = _item.last_in_movement.origin.stock_type if _item.last_in_movement else None

    return itens


@router.get("/list-byid/export/{client}/", response_model=Any)
async def export_items_by_client(
        client: str,
        status: str,
        db: Session = Depends(deps.get_db_psql),
        stock_type: str = None,
        # offset: int = 0,
        limit: int = 5000,
        locations_ids: Annotated[
            list[int] | None,
            Query(description="IDs das locations (pode repetir parâmetro)")
        ] = None,
):
    """
    # Consulta os items por client e status

    ### Opções de status:
    - `IN_DEPOT` -> Item no depósito
    - `IN_TRANSIT` -> Item em trânsito
    - `WITH_CLIENT` -> Item está em posse do contratante ou um de seus representantes
    - `WITH_CUSTOMER` -> Item está em posse do cliente final (instalado)

    ### Ao usar lista de locations_ids, retorna apenas items que estejam em uma das locations informadas:
    - Exemplo: `?locations_ids=1&locations_ids=2&locations_ids=11`
    """

    logger.info("Consultando products por client...")

    filters = [
        {"field": "status", "operator": "=", "value": status},
        {"field": "product.client.client_code", "operator": "=", "value": client},
    ]

    if locations_ids:
        filters.append({
            "field": "location.id",
            "operator": "in",
            "value": locations_ids  # já vem como lista[int]
        })
    if stock_type:
        filters.append({
            "field": "last_in_movement.origin.stock_type",
            "operator": "=",
            "value": stock_type
        })
    result = await item.get_multi_filters(
        db=db,
        filters=filters,
        order_by="created_at",
        order_desc=True,
        distinct_on_id=True,  # ativa DISTINCT ON (Item.id)
        # offset=offset,
        limit=limit,
    )
    from_locations_str = ''
    for _item in result:
        _item.location_name = F'{_item.location.cod_iata}-{_item.location.nome}' if _item.location.cod_iata else _item.location.nome
        _item.location_deps = _item.location.deposito if _item.location.deposito else None
        _item.product_sku = _item.product.sku
        _item.product_description = _item.product.description
        _item.produtct_category = _item.product.category
        _item.last_movement_in_date = _item.last_in_movement.created_at if _item.last_in_movement else None
        _item.stock_type = _item.last_in_movement.origin.stock_type if _item.last_in_movement else None
        if from_locations_str != '':
            from_locations_str += f'_and_{_item.location_name}' if _item.location_name not in from_locations_str else ''
        else:
            from_locations_str = f'_from_{_item.location_name}'

        # itero todos os objetos dentro de item.extra_info e crio eles e seus valores como colunas
        extra_info = _item.extra_info or {}

        if isinstance(extra_info, dict) and extra_info:
            flat_extra = flatten_dict(extra_info)

            for key, value in flat_extra.items():
                # normaliza o nome da "coluna"
                attr_name = f"extra_{key}".lower()

                # seta dinamicamente no item
                setattr(_item, attr_name, value)

    # === Converter para DataFrame ===
    data = [r.__dict__ for r in result]
    for d in data:
        d.pop('_sa_instance_state', None)

    df = pd.DataFrame(data)
    if client == 'cielo':
        ordered_columns = list(ItemInDbListBaseCielo.__fields__.keys())
    else:
        ordered_columns = list(ItemInDbListBase.__fields__.keys())
    df = df.reindex(columns=ordered_columns)

    for col in df.select_dtypes(include=["datetimetz"]).columns:
        df[col] = df[col].dt.tz_localize(None)

    # === Gerar Excel com formatação ===
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="IN_DEPOT_ITEMS")

    output.seek(0)

    now = datetime.now()
    filename = f"stock{from_locations_str}_{now.strftime('%d%m%y_%H%M')}.xlsx"

    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/list/{client}", response_model=List[ItemInDbBase])
async def read_items_by_client(
        client: str,
        status: str,
        sales_channels: Annotated[list[str] | None,
                                  Query(alias="sales_channels[]")] = None,
        db: Session = Depends(deps.get_db_psql)
) -> Any:
    """
    # Consulta os items por client e status

    ### Opções de status::
    - `IN_DEPOT` -> Item no depósito
    - `IN_TRANSIT` -> Item em trânsito
    - `WITH_CLIENT` -> Item está em posse do contratante ou um de seus representantes
    - `WITH_CUSTOMER` -> Item está em posse do cliente final, ou seja, instalado
    """
    logger.info("Consultando products por client...")
    filters = [
        {"field": "status", "operator": "=", "value": status},
        {"field": "product.client.client_code", "operator": "=", "value": client},
    ]
    if sales_channels:
        filters.append({"field": "location.sales_channel",
                       "operator": "in", "value": sales_channels})

    itens = await item.get_multi_filters(
        db=db,
        filters=filters,
        order_by="created_at",
        order_desc=True,
        distinct_on_id=True,  # <--- ativa DISTINCT ON (Item.id)
    )
    return itens


@router.get("/{serial}", response_model=ItemInDbListBase)
async def read_item(
        client: str,
        serial: str,
        db: Session = Depends(deps.get_db_psql)
) -> Any:
    """
    # Consulta um item por client e serial
    """
    logger.info("Consultando products por client...")
    filters = {
        'serial': {'operator': '==', 'value': serial},
        'product.client.client_code': {'operator': '==', 'value': client}
    }

    _item = await item.get_last_by_filters(
        db=db,
        filters=filters,
    )
    if not _item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found (O serial informado não existe ou não pertence a este cliente)",
        )

    _item.location_name = F'{_item.location.cod_iata}-{_item.location.nome}' if _item.location.cod_iata else _item.location.nome
    _item.product_sku = _item.product.sku
    _item.product_description = _item.product.description
    _item.produtct_category = _item.product.category
    _item.last_movement_in_date = _item.last_in_movement.created_at if _item.last_in_movement else None
    _item.stock_type = _item.last_in_movement.origin.stock_type if _item.last_in_movement else None

    return _item


@router.get("/{serial}/pedido", response_model=ItemPedidoInDbBase)
async def read_item(
        client: str,
        serial: str,
        db: Session = Depends(deps.get_db_psql)
) -> Any:
    """
    # Consulta um item por client e serial e retorna o pedido do movimento
    """
    logger.info("Consultando products por client...")
    filters = {
        'serial': {'operator': '==', 'value': serial},
        'product.client.client_code': {'operator': '==', 'value': client}
    }

    itens = await item.get_last_by_filters(
        db=db,
        filters=filters,
    )
    if not itens:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found (O serial informado não existe ou não pertence a este cliente)",
        )

    movimento = await movement.get_last_by_filters(
        db=db,
        filters={
            'item_id': {'operator': '==', 'value': itens.id}
        }
    )
    if movimento.movement_type != 'IN':
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item sem pedido (O item não possui um movimento de entrada associado)",
        )

    itens.in_order_number = movimento.order_number

    return itens


@router.put(path="/{id}", response_model=ItemInDbBase)
async def put_item(
        *,
        db: Session = Depends(deps.get_db_psql),
        id: int,
        payload: ItemProductUpdate
) -> Any:
    """
    # Atualiza informações de um produto existente
    ### CUIDADO: Essa ação é irreversível!
    """
    _item = await item.get(db=db, id=id)
    if not _item:
        raise HTTPException(status_code=404, detail="item not found")

    logger.info("Atualizando item...")
    _item = await item.update(db=db, db_obj=_item, obj_in=payload)
    return _item


@router.get("/delivery/{serial}", response_model=ItemInRetornoPickingBase)
async def read_item(
        client: str,
        serial: str,
        db: Session = Depends(deps.get_db_psql)
) -> Any:
    """
    #Consulta para uso do retorno do picking
    """
    # Rodo o upper do serial para ficar tudo caixa alta

    if client != 'cielo':
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Endpoint disponível apenas para o cliente CIELO",
        )

    serial = serial.upper()
    logger.info("Consultando products por client...")
    filters = {
        'serial': {'operator': '==', 'value': serial},
        'product.client.client_code': {'operator': '==', 'value': client}
    }

    _item = await item.get_last_by_filters(
        db=db,
        filters=filters,
    )
    if not _item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found (O serial informado não existe ou não pertence a este cliente)",
        )

    cons_sinc_service = ConsultaSincrona()
    consulta_sincrona: ResponseConsultaSincSC = await cons_sinc_service.executar_by_serial(serial)

    # valido se o depósito do item é o mesmo da consulta síncrona, se não for, retorno erro
    if _item.location.deposito != consulta_sincrona.LGORT:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Item {serial} está no depósito ({_item.location.deposito}) que é diferente do depósito SAP ({consulta_sincrona.LGORT}).",
        )

    # valido se o serial está em depósito no SAP. Se não estiver, retorno erro
    if not (consulta_sincrona.STTXU.strip() == 'DESN' and consulta_sincrona.STTXT.strip() == 'DEPS'):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Item com serial {serial} não está em depósito no SAP. Status SAP: {consulta_sincrona.STTXT} - {consulta_sincrona.STTXU}",
        )

    _item.product_sku = _item.product.sku
    _item.product_description = _item.product.description
    _item.produtct_category = _item.product.category

    _item.required_chip = True if _item.product.category != 'PINPAD' else False
    # verifico se o item possui extra_info preenchido com {"integration-ip": {"original_code": "207"}}
    if _item.required_chip and _item.last_in_movement.extra_info and 'integration-ip' in _item.last_in_movement.extra_info and 'original_code' in _item.last_in_movement.extra_info['integration-ip']:
        chip_item = await item.get_last_by_filters(
            db=db,
            filters={
                'product.client.client_code': {'operator': '==', 'value': 'cielo'},
                'product.category': {'operator': '==', 'value': 'CHIP'},
                'last_out_movement.order_number': {'operator': '==', 'value': _item.last_in_movement.order_number}
            }
        )
        if chip_item:
            _item.chip_serial = chip_item.serial

    return _item
