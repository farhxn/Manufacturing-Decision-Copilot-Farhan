"""Scenario repository."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.scenario import Scenario, ScenarioResult


class ScenarioRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_by_project(self, project_id: str) -> list[Scenario]:
        result = await self.session.execute(
            select(Scenario)
            .where(Scenario.project_id == project_id)
            .order_by(Scenario.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_by_id(self, scenario_id: str) -> Scenario | None:
        result = await self.session.execute(
            select(Scenario)
            .where(Scenario.id == scenario_id)
            .options(selectinload(Scenario.results).selectinload(ScenarioResult.supplier))
        )
        return result.scalar_one_or_none()

    async def create(self, scenario: Scenario) -> Scenario:
        self.session.add(scenario)
        await self.session.flush()
        await self.session.refresh(scenario)
        return scenario

    async def replace_results(
        self,
        scenario: Scenario,
        results: list[ScenarioResult],
    ) -> None:
        scenario.results.clear()
        await self.session.flush()
        for result in results:
            self.session.add(result)

    async def delete(self, scenario: Scenario) -> None:
        await self.session.delete(scenario)
