"""Evidence repository."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.document import DocumentChunk
from app.models.recommendation import Recommendation, RecommendationEvidence


class EvidenceRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_recommendation_id(
        self,
        recommendation_id: str,
    ) -> list[RecommendationEvidence]:
        result = await self.session.execute(
            select(RecommendationEvidence)
            .where(RecommendationEvidence.recommendation_id == recommendation_id)
            .options(
                selectinload(RecommendationEvidence.chunk).selectinload(DocumentChunk.document)
            )
            .order_by(RecommendationEvidence.relevance_score.desc())
        )
        return list(result.scalars().all())

    async def get_recommendation(self, recommendation_id: str) -> Recommendation | None:
        result = await self.session.execute(
            select(Recommendation).where(Recommendation.id == recommendation_id)
        )
        return result.scalar_one_or_none()

    async def bulk_create_evidence_items(
        self,
        items: list[RecommendationEvidence],
    ) -> None:
        """
        Persist a list of RecommendationEvidence rows in a single flush.

        Parameters
        ----------
        items:
            Pre-constructed ORM objects with recommendation_id, chunk_id,
            relevance_score, and snippet already set.
        """
        if not items:
            return
        self.session.add_all(items)
        await self.session.flush()
