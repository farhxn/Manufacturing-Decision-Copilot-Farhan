"""Supplier repository."""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.supplier import Supplier


class SupplierRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    def _base_query(self):
        return select(Supplier).options(
            selectinload(Supplier.capabilities),
            selectinload(Supplier.certifications),
            selectinload(Supplier.prices),
            selectinload(Supplier.risk_scores),
        )

    async def list_by_project(
        self,
        project_id: str,
        *,
        limit: int = 100,
        offset: int = 0,
        search: str | None = None,
        country: str | None = None,
    ) -> list[Supplier]:
        stmt = self._base_query().where(Supplier.project_id == project_id)
        if search:
            stmt = stmt.where(Supplier.name.ilike(f"%{search}%"))
        if country:
            stmt = stmt.where(Supplier.country.ilike(country))
        stmt = stmt.order_by(Supplier.name.asc()).offset(offset).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def count_by_project(
        self,
        project_id: str,
        *,
        search: str | None = None,
        country: str | None = None,
    ) -> int:
        stmt = select(func.count(Supplier.id)).where(Supplier.project_id == project_id)
        if search:
            stmt = stmt.where(Supplier.name.ilike(f"%{search}%"))
        if country:
            stmt = stmt.where(Supplier.country.ilike(country))
        result = await self.session.execute(stmt)
        return int(result.scalar_one())

    async def get_by_id(self, supplier_id: str) -> Supplier | None:
        result = await self.session.execute(
            self._base_query().where(Supplier.id == supplier_id)
        )
        return result.scalar_one_or_none()

    async def get_by_ids(self, supplier_ids: list[str]) -> list[Supplier]:
        if not supplier_ids:
            return []
        result = await self.session.execute(
            self._base_query().where(Supplier.id.in_(supplier_ids))
        )
        return list(result.scalars().all())

    async def create(self, supplier: Supplier) -> Supplier:
        self.session.add(supplier)
        await self.session.flush()
        # Fetch it again to properly load all relationships (prices, etc.) 
        # in the async context without triggering lazy load errors.
        reloaded = await self.get_by_id(supplier.id)
        if not reloaded:
            raise RuntimeError("Failed to reload supplier after create")
        return reloaded

    async def update(self, supplier: Supplier, update_data: dict) -> Supplier:
        for key, value in update_data.items():
            setattr(supplier, key, value)
        await self.session.flush()
        reloaded = await self.get_by_id(supplier.id)
        if not reloaded:
            raise RuntimeError("Failed to reload supplier after update")
        return reloaded

    async def delete(self, supplier: Supplier) -> None:
        await self.session.delete(supplier)
        await self.session.flush()
