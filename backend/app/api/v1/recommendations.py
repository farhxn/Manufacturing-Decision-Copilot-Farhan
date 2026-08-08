"""Recommendation API routes."""

from fastapi import APIRouter, Depends, Query

from app.core.dependencies import get_recommendation_service
from app.core.exceptions import AppHTTPException
from app.schemas.common import APIResponse
from app.schemas.recommendation import RecommendationSchema
from app.services.recommendation_service import RecommendationService

router = APIRouter(prefix="/recommendations", tags=["Recommendations"])

DEFAULT_PROJECT_ID = "00000000-0000-4000-a000-000000000002"


@router.get("", response_model=APIResponse[RecommendationSchema])
async def get_recommendation(
    project_id: str = Query(DEFAULT_PROJECT_ID),
    service: RecommendationService = Depends(get_recommendation_service),
):
    recommendation = await service.get_recommendation(project_id)
    if not recommendation:
        raise AppHTTPException(
            status_code=404,
            code="RECOMMENDATION_NOT_FOUND",
            message=f"No recommendation could be generated for project {project_id}.",
        )
    return APIResponse(
        success=True,
        message="Recommendation retrieved successfully.",
        data=recommendation,
    )


@router.post("/regenerate", response_model=APIResponse[RecommendationSchema])
async def regenerate_recommendation(
    project_id: str = Query(DEFAULT_PROJECT_ID),
    service: RecommendationService = Depends(get_recommendation_service),
):
    recommendation = await service.regenerate(project_id)
    if not recommendation:
        raise AppHTTPException(
            status_code=404,
            code="RECOMMENDATION_NOT_FOUND",
            message=f"No recommendation could be generated for project {project_id}.",
        )
    return APIResponse(
        success=True,
        message="Recommendation regenerated successfully.",
        data=recommendation,
    )
