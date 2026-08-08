"""Evidence API routes."""

from fastapi import APIRouter, Depends

from app.core.dependencies import get_evidence_service
from app.core.exceptions import AppHTTPException
from app.schemas.common import APIResponse
from app.schemas.evidence import EvidenceListSchema
from app.services.evidence_service import EvidenceService

router = APIRouter(prefix="/evidence", tags=["Evidence"])


@router.get("/{recommendation_id}", response_model=APIResponse[EvidenceListSchema])
async def get_evidence(
    recommendation_id: str,
    service: EvidenceService = Depends(get_evidence_service),
):
    evidence = await service.get_by_recommendation_id(recommendation_id)
    if not evidence:
        raise AppHTTPException(
            status_code=404,
            code="RECOMMENDATION_NOT_FOUND",
            message=f"Recommendation {recommendation_id} was not found.",
        )
    return APIResponse(
        success=True,
        message="Evidence retrieved successfully.",
        data=evidence,
    )
