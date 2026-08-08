"""Evidence business service."""

from app.repositories.evidence_repository import EvidenceRepository
from app.schemas.evidence import EvidenceItemSchema, EvidenceListSchema


class EvidenceService:
    def __init__(self, evidence_repo: EvidenceRepository):
        self.evidence_repo = evidence_repo

    async def get_by_recommendation_id(
        self,
        recommendation_id: str,
    ) -> EvidenceListSchema | None:
        recommendation = await self.evidence_repo.get_recommendation(recommendation_id)
        if not recommendation:
            return None

        evidence_items = await self.evidence_repo.get_by_recommendation_id(recommendation_id)
        items = []
        for evidence in evidence_items:
            document = evidence.chunk.document if evidence.chunk else None
            items.append(
                EvidenceItemSchema(
                    id=evidence.id,
                    chunk_id=evidence.chunk_id,
                    document_id=document.id if document else None,
                    document_filename=document.filename if document else None,
                    snippet=evidence.snippet,
                    relevance_score=evidence.relevance_score,
                    page_number=evidence.chunk.page_number if evidence.chunk else None,
                )
            )

        return EvidenceListSchema(
            recommendation_id=recommendation_id,
            items=items,
        )
