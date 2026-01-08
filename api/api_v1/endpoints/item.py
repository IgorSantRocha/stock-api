from datetime import datetime
from io import BytesIO
from typing import Any, List, Annotated
import logging
from collections import defaultdict
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import StreamingResponse
import pandas as pd
from sqlalchemy.orm import Session

from crud.crud_movement import movement
from crud.crud_item import item
from schemas.item_resume_schema import PaStockResumeSchema

from schemas.item_schema import ItemCreate, ItemInDbListBase, ItemProductUpdate, ItemUpdate, ItemInDbBase, ItemPedidoInDbBase


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
        pa = row["cod_iata"]
        st = row["stock_type"]

        result[pa][st] = {
            "type": st,
            "total": row["total"],
            "qtd_por_produto": {},
            "qtd_por_ztipo": {}
        }

    # ---- produtos
    for row in por_produto:
        pa = row["cod_iata"]
        st = row["stock_type"]
        sku = row["sku"]
        description = row["description"]
        txt = f"{sku} - {description}"

        if pa in result and st in result[pa]:
            result[pa][st]["qtd_por_produto"][txt] = row["qtd"]

    # ---- ztipo (JSON)
    for row in por_ztipo:
        pa = row["cod_iata"]
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
        _item.location_name = f'PA_{_item.location.cod_iata}-{_item.location.nome}' if _item.location.cod_iata else _item.location.nome
        _item.product_sku = _item.product.sku
        _item.product_description = _item.product.description
        _item.produtct_category = _item.product.category
        _item.last_movement_in_date = _item.last_in_movement.created_at if _item.last_in_movement else None
        _item.stock_type = _item.last_in_movement.origin.stock_type if _item.last_in_movement else None

    return itens


@router.get("/list-byid/export/{client}/", response_model=List[ItemInDbListBase])
async def export_items_by_client(
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
        offset=offset,
        limit=limit,
    )
    from_locations_str = ''
    for _item in result:
        _item.location_name = f'PA_{_item.location.cod_iata}-{_item.location.nome}' if _item.location.cod_iata else _item.location.nome
        _item.product_sku = _item.product.sku
        _item.product_description = _item.product.description
        _item.produtct_category = _item.product.category
        _item.last_movement_in_date = _item.last_in_movement.created_at if _item.last_in_movement else None
        _item.stock_type = _item.last_in_movement.origin.stock_type if _item.last_in_movement else None
        if from_locations_str != '':
            from_locations_str += f'_and_{_item.location_name}' if _item.location_name not in from_locations_str else ''
        else:
            from_locations_str = f'_from_{_item.location_name}'

    # === Converter para DataFrame ===
    data = [r.__dict__ for r in result]
    for d in data:
        d.pop('_sa_instance_state', None)

    df = pd.DataFrame(data)
    ordered_columns = list(ItemInDbListBase.__fields__.keys())
    df = df.reindex(columns=ordered_columns)

    for col in df.select_dtypes(include=["datetimetz"]).columns:
        df[col] = df[col].dt.tz_localize(None)

    # === Gerar Excel com formatação ===
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="IN_DEPOT_ITEMS")
        # ws = writer.sheets["Pedidos"]

    #     # Encontrar índice da coluna 'ultima_tracking'
    #     col_index = None
    #     for idx, col_name in enumerate(df.columns, 1):
    #         if col_name == "ultima_tracking":
    #             col_index = idx
    #             break

    # # Aplicar cor vermelha escura nas células com "TROCA DE CUSTODIA PENDENTE"
    # if col_index:
    #     # começa na linha 2 (depois do cabeçalho)
    #     for row_idx, value in enumerate(df["ultima_tracking"], start=2):
    #         if value == "TROCA DE CUSTODIA PENDENTE":
    #             ws.cell(row=row_idx, column=col_index).font = Font(
    #                 color="8B0000", bold=True)

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
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found (O serial informado não existe ou não pertence a este cliente)",
        )

    _item.location_name = f'PA_{_item.location.cod_iata}-{_item.location.nome}' if _item.location.cod_iata else _item.location.nome
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
