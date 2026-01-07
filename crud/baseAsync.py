import logging
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import desc, and_
from db.base_class import Base
from sqlalchemy import func, select,  cast
from sqlalchemy.types import Numeric
from sqlalchemy.dialects.postgresql import JSON, JSONB
from sqlalchemy.sql.elements import ColumnElement

ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    def __init__(self, model: Type[ModelType]):
        self.model = model

    # ----------------------
    # Helpers para relações
    # ----------------------

    def _normalize_like(self, op: str, value: Any) -> Any:
        if op in ("like", "ilike") and isinstance(value, str):
            if "%" not in value and "_" not in value:
                return f"%{value}%"
        return value

    def _resolve_and_join(
        self,
        stmt,
        dotted_field: str,
        join_tracker: Dict[str, bool]
    ):
        """
        Resolve:
        - campo
        - rel1.rel2.campo
        - json_field.chave.subchave

        SEMPRE mantém current_model como classe de modelo.
        """

        parts = dotted_field.split(".")
        current_model = self.model
        path_accum = []

        # =========================
        # Campo simples
        # =========================
        if len(parts) == 1:
            attr = getattr(current_model, parts[0], None)
            if attr is None:
                raise ValueError(
                    f"Campo '{parts[0]}' não existe em {current_model.__name__}."
                )
            return stmt, attr

        # =========================
        # Caminho completo
        # =========================
        for idx, part in enumerate(parts):
            # -------------------------
            # Último campo → coluna
            # -------------------------
            if idx == len(parts) - 1:
                attr = getattr(current_model, part, None)
                if attr is None:
                    raise ValueError(
                        f"Coluna '{part}' não existe em {current_model.__name__}."
                    )
                return stmt, attr

            # -------------------------
            # Atributo do modelo
            # -------------------------
            attr = getattr(current_model, part, None)

            # =========================
            # JSON / JSONB
            # =========================
            if attr is not None and hasattr(attr, "type") and isinstance(attr.type, (JSON, JSONB)):
                json_attr: ColumnElement = attr

                for json_key in parts[idx + 1:-1]:
                    json_attr = json_attr[json_key]

                last_key = parts[-1]
                return stmt, json_attr[last_key].astext

            # =========================
            # RELATIONSHIP
            # =========================
            rel = current_model.__mapper__.relationships.get(part)
            if rel is None:
                raise ValueError(
                    f"Campo ou relacionamento '{part}' não existe em {current_model.__name__}."
                )

            path_accum.append(part)
            path_key = ".".join(path_accum)

            if not join_tracker.get(path_key):
                stmt = stmt.join(getattr(current_model, part))
                join_tracker[path_key] = True

            # 🔑 SEMPRE usar a classe do relacionamento
            current_model = rel.mapper.class_

        raise ValueError(f"Caminho inválido: {dotted_field}")

    def _resolve_and_join_depreceated(self, stmt, dotted_field: str, join_tracker: Dict[str, bool]):
        """
        Aceita "campo" ou "rel1.rel2.campo". Faz JOIN nas relações conforme necessário
        e retorna (stmt_atualizado, atributo_SQLAlchemy).
        """
        parts = dotted_field.split(".")
        current_model = self.model

        # Campo simples
        if len(parts) == 1:
            attr = getattr(current_model, parts[0], None)
            if attr is None:
                raise ValueError(
                    f"Campo '{parts[0]}' não existe em {current_model.__name__}.")
            return stmt, attr

        # Caminho relacionado (suporta múltiplos níveis)
        path_accum = []
        for rel_name in parts[:-1]:
            path_accum.append(rel_name)
            path_key = ".".join(path_accum)

            rel = current_model.__mapper__.relationships.get(rel_name)
            if rel is None:
                raise ValueError(
                    f"Relacionamento '{rel_name}' não existe em {current_model.__name__}."
                )

            if not join_tracker.get(path_key):
                stmt = stmt.join(getattr(current_model, rel_name))
                join_tracker[path_key] = True

            current_model = rel.entity.class_

        # Último pedaço é a coluna
        col_name = parts[-1]
        attr = getattr(current_model, col_name, None)
        if attr is None:
            raise ValueError(
                f"Coluna '{col_name}' não existe em {current_model.__name__}.")
        return stmt, attr

    # Mapa de operadores para get_multi_filters / get_last_by_filters
    _OP = {
        "=": lambda f, v: f == v,
        "==": lambda f, v: f == v,   # sinônimo
        "!=": lambda f, v: f != v,
        "<": lambda f, v: f < v,
        "<=": lambda f, v: f <= v,
        ">": lambda f, v: f > v,
        ">=": lambda f, v: f >= v,
        "like": lambda f, v: f.like(v),
        "ilike": lambda f, v: f.ilike(v),
        "in": lambda f, v: f.in_(v),
        "notin": lambda f, v: ~f.in_(v),
        "is_null": lambda f, _: f.is_(None),
        "is_not_null": lambda f, _: f.is_not(None),
    }
    _AGG_OP = {
        "sum": func.sum,
        "count": func.count,
        "avg": func.avg,
        "min": func.min,
        "max": func.max,
    }

    async def get_aggregates(
        self,
        db: AsyncSession,
        *,
        filters: Optional[List[Dict[str, Any]]] = None,
        aggregations: List[Dict[str, Any]],
        group_by: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:

        join_tracker: Dict[str, bool] = {}
        stmt = select()
        select_columns = []
        group_columns = []

        # ==========================
        # AGGREGATIONS
        # ==========================
        for agg in aggregations:
            op = agg["op"]
            field = agg["field"]
            alias = agg.get("alias", f"{op}_{field}")
            is_json = agg.get("is_json", False)

            if op not in self._AGG_OP:
                raise ValueError(f"Agregação '{op}' não suportada.")

            stmt, attr = self._resolve_and_join(stmt, field, join_tracker)

            if is_json:
                # JSON → cast para número
                attr = cast(attr.astext, Numeric)

            select_columns.append(
                self._AGG_OP[op](attr).label(alias)
            )

        # ==========================
        # GROUP BY
        # ==========================
        if group_by:
            for gb in group_by:
                stmt, gb_attr = self._resolve_and_join(stmt, gb, join_tracker)
                label = gb.split(".")[-1]  # ZTIPO
                group_columns.append(gb_attr)
                select_columns.append(gb_attr.label(label))


            stmt = stmt.group_by(*group_columns)

        stmt = stmt.with_only_columns(*select_columns)

        # ==========================
        # FILTERS (reaproveita padrão)
        # ==========================
        conditions = []
        if filters:
            for f in filters:
                field = f["field"]
                op = f.get("operator", "=")
                value = f["value"]

                if op not in self._OP:
                    raise ValueError(f"Operador '{op}' não suportado.")

                value = self._normalize_like(op, value)
                stmt, attr = self._resolve_and_join(stmt, field, join_tracker)

                conditions.append(self._OP[op](attr, value))

        if conditions:
            stmt = stmt.where(and_(*conditions))

        # ==========================
        # EXEC
        # ==========================
        result = await db.execute(stmt)

        rows = result.mappings().all()
        return [dict(row) for row in rows]

    # ----------------------
    # GETs adaptados
    # ----------------------
    async def get(self, db: AsyncSession, id: Any) -> Optional[ModelType]:
        stmt = select(self.model).filter(self.model.id == id)
        result = await db.execute(stmt)
        # não precisa de join; mas unique() é inofensivo
        return result.scalars().unique().first()

    async def get_first_by_filter(
        self, db: AsyncSession, *, order_by: str = "id", filterby: str = "enviado", filter: str
    ) -> Optional[ModelType]:
        join_tracker: Dict[str, bool] = {}
        stmt = select(self.model)

        # WHERE
        stmt, where_attr = self._resolve_and_join(stmt, filterby, join_tracker)
        stmt = stmt.where(where_attr == filter)

        # ORDER BY
        stmt, order_attr = self._resolve_and_join(stmt, order_by, join_tracker)
        stmt = stmt.order_by(order_attr)

        result = await db.execute(stmt)
        return result.scalars().unique().first()

    async def get_multi(
        self, db: AsyncSession, *, skip: int = 0, limit: int = 100, order_by: str = "id"
    ) -> List[ModelType]:
        join_tracker: Dict[str, bool] = {}
        stmt = select(self.model)

        # ORDER BY (suporta relação)
        stmt, order_attr = self._resolve_and_join(stmt, order_by, join_tracker)
        stmt = stmt.order_by(order_attr).offset(skip).limit(limit)

        result = await db.execute(stmt)
        return result.scalars().unique().all()

    async def get_multi_filter(
        self, db: AsyncSession, *, order_by: str = "id", filterby: str = "enviado", filter: str
    ) -> List[ModelType]:
        join_tracker: Dict[str, bool] = {}
        stmt = select(self.model)

        # WHERE
        stmt, where_attr = self._resolve_and_join(stmt, filterby, join_tracker)
        stmt = stmt.where(where_attr == filter)

        # ORDER BY
        stmt, order_attr = self._resolve_and_join(stmt, order_by, join_tracker)
        stmt = stmt.order_by(order_attr)

        result = await db.execute(stmt)
        return result.scalars().unique().all()

    async def get_multi_filters(
        self,
        db: AsyncSession,
        *,
        filters: List[Dict[str, Any]],
        order_by: Optional[str] = None,
        order_desc: bool = False,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        distinct_on_id: bool = False,
    ) -> List[ModelType]:
        join_tracker: Dict[str, bool] = {}
        stmt = select(self.model)

        conditions = []
        for f in filters:
            field = f["field"]
            op = f.get("operator", "=")
            value = f["value"]

            if op not in self._OP:
                raise ValueError(f"Operador '{op}' não suportado.")

            value = self._normalize_like(op, value)
            stmt, attr = self._resolve_and_join(stmt, field, join_tracker)

            if op in ("in", "notin") and not isinstance(value, (list, tuple, set)):
                raise ValueError(f"Operador '{op}' exige lista/tupla.")

            conditions.append(self._OP[op](attr, value))

        if conditions:
            stmt = stmt.where(and_(*conditions))

        # ORDER BY
        order_clause = None
        if order_by:
            stmt, order_attr = self._resolve_and_join(
                stmt, order_by, join_tracker)
            order_clause = order_attr.desc() if order_desc else order_attr.asc()

        if distinct_on_id:
            stmt = stmt.distinct(self.model.id)
            if order_clause is not None:
                stmt = stmt.order_by(self.model.id, order_clause)
            else:
                stmt = stmt.order_by(self.model.id)
        else:
            if order_clause is not None:
                stmt = stmt.order_by(order_clause)

        if offset:
            stmt = stmt.offset(offset)
        if limit:
            stmt = stmt.limit(limit)

        result = await db.execute(stmt)
        return result.scalars().unique().all()

    async def get_last_by_filters(
        self, db: AsyncSession, *, filters: Dict[str, Dict[str, Union[str, int]]]
    ) -> Optional[ModelType]:
        """
        filters esperado:
        {
          "status": {"operator": "==", "value": "IN_DEPOT"},
          "product.client_name": {"operator": "ilike", "value": "cielo"}
        }
        """
        join_tracker: Dict[str, bool] = {}
        stmt = select(self.model)

        conditions = []
        for field, condition in filters.items():
            op = condition["operator"]
            op = '=' if op == '==' else op
            value = condition.get("value")

            if op not in self._OP:
                raise ValueError(f"Operador '{op}' não suportado.")

            value = self._normalize_like(op, value)
            stmt, attr = self._resolve_and_join(stmt, field, join_tracker)

            if op in ("in", "notin") and not isinstance(value, (list, tuple, set)):
                raise ValueError(
                    f"Operador '{op}' exige lista/tupla de valores.")

            conditions.append(self._OP[op](attr, value))

        if conditions:
            stmt = stmt.where(and_(*conditions))

        # último por id desc
        stmt = stmt.order_by(desc(self.model.id))

        result = await db.execute(stmt)
        obj = result.scalars().unique().first()
        if obj:
            await db.refresh(obj)
        return obj

    # ----------------------
    # CRUD write (inalterado)
    # ----------------------
    async def create(self, db: AsyncSession, *, obj_in: CreateSchemaType) -> ModelType:
        obj_data = obj_in.model_dump()
        db_obj = self.model(**obj_data)  # type: ignore
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def create_multi(self, db: AsyncSession, *, obj_in: List[CreateSchemaType]) -> Dict[str, str]:
        db_objs = [self.model(**jsonable_encoder(obj)) for obj in obj_in]
        db.add_all(db_objs)
        await db.commit
        return {"msg": "Objetos criados com sucesso"}

    async def update(
        self,
        db: AsyncSession,
        *,
        db_obj: ModelType,
        obj_in: Union[UpdateSchemaType, Dict[str, Any]]
    ) -> ModelType:
        update_data = obj_in if isinstance(
            obj_in, dict) else obj_in.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def update_multi(
        self,
        db: AsyncSession,
        *,
        objs_in: List[Union[UpdateSchemaType, Dict[str, Any]]],
        filtro: str
    ) -> List[ModelType]:
        updated_objs = []
        for obj_in in objs_in:
            data = obj_in if isinstance(
                obj_in, dict) else obj_in.dict(exclude_unset=True)
            filtro_valor = data[filtro]
            stmt = select(self.model).where(
                getattr(self.model, filtro) == filtro_valor)
            result = await db.execute(stmt)
            db_obj = result.scalars().first()
            if db_obj:
                for key, value in data.items():
                    setattr(db_obj, key, value)
                await db.commit()
                await db.refresh(db_obj)
                updated_objs.append(db_obj)
        return updated_objs

    async def remove(self, db: AsyncSession, *, id: int) -> Optional[ModelType]:
        stmt = select(self.model).where(self.model.id == id)
        result = await db.execute(stmt)
        obj = result.scalars().first()
        if obj:
            await db.delete(obj)
            await db.commit()
        return obj
