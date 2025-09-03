from typing import Any, Dict, List, Optional
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from crud.baseAsync import CRUDBase
from models.item_model import Item
from models.product_model import Product   # ajuste o caminho se necessário
from models.location_model import Location  # ajuste o caminho se necessário
from schemas.item_schema import ItemCreate, ItemUpdate


class CRUDItem(CRUDBase[Item, ItemCreate, ItemUpdate]):
    """
    Filtros com notação pontilhada:
      - Campos do Item: "status", "serial", "created_at", ...
      - Campos de relações:
          "product.client_name" (JOIN em Item.product -> Product.client_name)
          "location.nome"       (JOIN em Item.location -> Location.nome)

    Operadores suportados: =, !=, <, <=, >, >=, like, ilike, in, notin
    (em like/ilike, se você passar "Acme" sem %, será convertido para "%Acme%")
    """

    _OP = {
        '=': lambda f, v: f == v,
        '!=': lambda f, v: f != v,
        '<': lambda f, v: f < v,
        '<=': lambda f, v: f <= v,
        '>': lambda f, v: f > v,
        '>=': lambda f, v: f >= v,
        'like': lambda f, v: f.like(v),
        'ilike': lambda f, v: f.ilike(v),
        'in': lambda f, v: f.in_(v),
        'notin': lambda f, v: ~f.in_(v),
    }

    def _auto_wrap_like(self, op: str, value: Any) -> Any:
        """Se for like/ilike e vier sem %/_, aplica %valor%."""
        if op in ('like', 'ilike') and isinstance(value, str):
            if '%' not in value and '_' not in value:
                return f"%{value}%"
        return value

    def _resolve_field(self, field: str):
        """
        Resolve o 'field' para um atributo SQLAlchemy.
        - Se for simples (sem ponto), retorna Item.<campo>.
        - Se for 'product.<campo>', retorna (alvo='product', attr=Product.<campo>).
        - Se for 'location.<campo>', retorna (alvo='location', attr=Location.<campo>).
        """
        if '.' not in field:
            return None, getattr(Item, field)

        rel, col = field.split('.', 1)
        if rel == 'product':
            return 'product', getattr(Product, col)
        elif rel == 'location':
            return 'location', getattr(Location, col)
        else:
            raise ValueError(f"Relacionamento '{rel}' não suportado nesta V1.")

    async def list_with_filters(
        self,
        db: AsyncSession,
        *,
        filters: List[Dict[str, Any]],
        order_by: Optional[str] = None,
        order_desc: bool = False,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        eager: bool = True,
        distinct_on_id: bool = False,  # <--- NOVO
    ) -> List[Item]:
        stmt = select(Item)

        if eager:
            stmt = stmt.options(
                selectinload(Item.product),
                selectinload(Item.location),
            )

        joined_product = False
        joined_location = False

        conditions = []
        for f in filters:
            field = f['field']
            op = f.get('operator', '=')
            value = self._auto_wrap_like(op, f['value'])

            if op not in self._OP:
                raise ValueError(f"Operador '{op}' não suportado.")

            rel, attr = self._resolve_field(field)
            if rel == 'product' and not joined_product:
                stmt = stmt.join(Item.product)
                joined_product = True
            elif rel == 'location' and not joined_location:
                stmt = stmt.join(Item.location)
                joined_location = True

            if op in ('in', 'notin') and not isinstance(value, (list, tuple, set)):
                raise ValueError(
                    f"Operador '{op}' exige lista/tupla de valores.")

            conditions.append(self._OP[op](attr, value))

        if conditions:
            stmt = stmt.where(and_(*conditions))

        # ORDER BY
        order_clause = None
        if order_by:
            rel, attr = self._resolve_field(order_by)
            if rel == 'product' and not joined_product:
                stmt = stmt.join(Item.product)
                joined_product = True
            elif rel == 'location' and not joined_location:
                stmt = stmt.join(Item.location)
                joined_location = True
            order_clause = attr.desc() if order_desc else attr.asc()

        # DISTINCT handling
        if distinct_on_id:
            # PostgreSQL: DISTINCT ON (Item.id) exige ORDER BY começando por Item.id
            stmt = stmt.distinct(Item.id)
            if order_clause is not None:
                stmt = stmt.order_by(Item.id, order_clause)
            else:
                stmt = stmt.order_by(Item.id)
        else:
            # sem DISTINCT para evitar erro com coluna JSON
            if order_clause is not None:
                stmt = stmt.order_by(order_clause)

        if offset:
            stmt = stmt.offset(offset)
        if limit:
            stmt = stmt.limit(limit)

        result = await db.execute(stmt)
        return result.scalars().unique().all()


# instância exportada
item = CRUDItem(Item)
