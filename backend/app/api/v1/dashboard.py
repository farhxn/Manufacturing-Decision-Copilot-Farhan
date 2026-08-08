"""Dashboard API routes."""

from fastapi import APIRouter, Depends, Query

from app.core.dependencies import get_dashboard_service
from app.core.exceptions import AppHTTPException
from app.schemas.common import APIResponse
from app.schemas.dashboard import DashboardSchema
from app.services.dashboard_service import DashboardService

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

DEFAULT_PROJECT_ID = "00000000-0000-4000-a000-000000000002"


@router.get("", response_model=APIResponse[DashboardSchema])
async def get_dashboard(
    project_id: str = Query(DEFAULT_PROJECT_ID),
    service: DashboardService = Depends(get_dashboard_service),
):
    dashboard = await service.get_dashboard(project_id)
    if not dashboard:
        raise AppHTTPException(
            status_code=404,
            code="PROJECT_NOT_FOUND",
            message=f"Dashboard data for project {project_id} was not found.",
        )
    return APIResponse(
        success=True,
        message="Dashboard retrieved successfully.",
        data=dashboard,
    )
