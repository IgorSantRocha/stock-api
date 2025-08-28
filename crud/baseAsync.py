import logging
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update, desc
from db.base_class import Base

ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class CRUDBaseAsync(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    def __init__(self, model: Type[ModelType]):
        self.model = model

    async def get(self, db: AsyncSession, id: Any) -> Optional[ModelType]:
        stmt = select(self.model).filter(self.model.id == id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_first_by_filter(
        self, db: AsyncSession, *, order_by: str = "id", filterby: str = "enviado", filter: str
    ) -> Optional[ModelType]:
        stmt = select(self.model).where(getattr(self.model, filterby) == filter).order_by(getattr(self.model, order_by))
        result = await db.execute(stmt)
        return result.scalars().first()

    async def get_multi(
        self, db: AsyncSession, *, skip: int = 0, limit: int = 100, order_by: str = "id"
    ) -> List[ModelType]:
        stmt = select(self.model).order_by(getattr(self.model, order_by)).offset(skip).limit(limit)
        result = await db.execute(stmt)
        return result.scalars().all()

    async def get_multi_filter(
        self, db: AsyncSession, *, order_by: str = "id", filterby: str = "enviado", filter: str
    ) -> List[ModelType]:
        stmt = select(self.model).where(getattr(self.model, filterby) == filter).order_by(getattr(self.model, order_by))
        result = await db.execute(stmt)
        return result.scalars().all()

    async def get_multi_filters(
        self, db: AsyncSession, *, filters: List[Dict[str, Any]]
    ) -> List[ModelType]:
        from sqlalchemy import and_

        operator_map = {
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

        conditions = []
        for f in filters:
            field = getattr(self.model, f['field'])
            operator = f.get('operator', '=')
            value = f['value']
            conditions.append(operator_map[operator](field, value))

        stmt = select(self.model).where(and_(*conditions))
        result = await db.execute(stmt)
        return result.scalars().all()

    async def get_last_by_filters(
        self, db: AsyncSession, *, filters: Dict[str, Dict[str, Union[str, int]]]
    ) -> Optional[ModelType]:
        stmt = select(self.model)
        for field, condition in filters.items():
            operator = condition["operator"]
            value = condition["value"]
            col = getattr(self.model, field)
            if operator == "==":
                stmt = stmt.where(col == value)
            elif operator == "!=":
                stmt = stmt.where(col != value)
            elif operator == ">":
                stmt = stmt.where(col > value)
            elif operator == "<":
                stmt = stmt.where(col < value)
            elif operator == ">=":
                stmt = stmt.where(col >= value)
            elif operator == "<=":
                stmt = stmt.where(col <= value)
            elif operator == "like":
                stmt = stmt.where(col.like(f"%{value}%"))
            elif operator == "is_null":
                stmt = stmt.where(col.is_(None))

        stmt = stmt.order_by(desc(self.model.id))
        result = await db.execute(stmt)
        return result.scalars().first()

    async def create(self, db: AsyncSession, *, obj_in: CreateSchemaType) -> ModelType:
        obj_data = jsonable_encoder(obj_in)
        db_obj = self.model(**obj_data)  # type: ignore
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def create_multi(self, db: AsyncSession, *, obj_in: List[CreateSchemaType]) -> Dict[str, str]:
        db_objs = [self.model(**jsonable_encoder(obj)) for obj in obj_in]
        db.add_all(db_objs)
        await db.commit()
        return {'msg': 'Objetos criados com sucesso'}

    async def update(
        self,
        db: AsyncSession,
        *,
        db_obj: ModelType,
        obj_in: Union[UpdateSchemaType, Dict[str, Any]]
    ) -> ModelType:
        update_data = obj_in if isinstance(obj_in, dict) else obj_in.dict(exclude_unset=True)
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
            data = obj_in if isinstance(obj_in, dict) else obj_in.dict(exclude_unset=True)
            filtro_valor = data[filtro]
            stmt = select(self.model).where(getattr(self.model, filtro) == filtro_valor)
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
