"""Report repository — database I/O only."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.report import Report


class ReportRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, report: Report) -> Report:
        self._session.add(report)
        await self._session.flush()
        await self._session.refresh(report)
        return report

    async def get_by_id(self, report_id: str) -> Report | None:
        result = await self._session.execute(
            select(Report).where(Report.id == report_id)
        )
        return result.scalar_one_or_none()

    async def list_by_project(
        self,
        project_id: str,
        limit: int = 20,
        offset: int = 0,
    ) -> list[Report]:
        result = await self._session.execute(
            select(Report)
            .where(Report.project_id == project_id)
            .order_by(Report.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    async def delete(self, report_id: str) -> bool:
        report = await self.get_by_id(report_id)
        if not report:
            return False
        await self._session.delete(report)
        await self._session.flush()
        return True
