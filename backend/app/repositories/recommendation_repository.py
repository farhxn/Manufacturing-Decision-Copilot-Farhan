"""Recommendation repository."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.recommendation import Recommendation, RecommendationEvidence


class RecommendationRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_latest_for_project(self, project_id: str) -> Recommendation | None:
        result = await self.session.execute(
            select(Recommendation)
            .where(Recommendation.project_id == project_id)
            .options(
                selectinload(Recommendation.recommended_supplier),
                selectinload(Recommendation.evidence_items).selectinload(
                    RecommendationEvidence.chunk
                ),
            )
            .order_by(Recommendation.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def create(self, recommendation: Recommendation) -> Recommendation:
        self.session.add(recommendation)
        await self.session.flush()
        await self.session.refresh(recommendation)
        return recommendation
