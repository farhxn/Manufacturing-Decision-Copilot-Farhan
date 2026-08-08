"""Project API routes."""

from fastapi import APIRouter, Depends

from app.core.dependencies import get_project_service
from app.core.exceptions import AppHTTPException
from app.schemas.common import APIResponse
from app.schemas.project import ProjectCreateSchema, ProjectUpdateSchema, ProjectSchema
from app.services.project_service import ProjectService

router = APIRouter(prefix="/projects", tags=["Projects"])

DEFAULT_ORG_ID = "00000000-0000-4000-a000-000000000001"


@router.get("", response_model=APIResponse[list[ProjectSchema]])
async def list_projects(
    service: ProjectService = Depends(get_project_service),
):
    projects = await service.list_projects(DEFAULT_ORG_ID)
    return APIResponse(
        success=True,
        message="Projects retrieved successfully.",
        data=projects,
    )


@router.get("/{project_id}", response_model=APIResponse[ProjectSchema])
async def get_project(
    project_id: str,
    service: ProjectService = Depends(get_project_service),
):
    project = await service.get_project(project_id)
    if not project:
        raise AppHTTPException(
            status_code=404,
            code="PROJECT_NOT_FOUND",
            message=f"Project {project_id} was not found.",
        )
    return APIResponse(
        success=True,
        message="Project retrieved successfully.",
        data=project,
    )


@router.post("", response_model=APIResponse[ProjectSchema], status_code=201)
async def create_project(
    payload: ProjectCreateSchema,
    service: ProjectService = Depends(get_project_service),
):
    project = await service.create_project(DEFAULT_ORG_ID, payload)
    return APIResponse(
        success=True,
        message="Project created successfully.",
        data=project,
    )


@router.patch("/{project_id}", response_model=APIResponse[ProjectSchema])
async def update_project(
    project_id: str,
    payload: ProjectUpdateSchema,
    service: ProjectService = Depends(get_project_service),
):
    project = await service.update_project(project_id, payload)
    if not project:
        raise AppHTTPException(
            status_code=404,
            code="PROJECT_NOT_FOUND",
            message=f"Project {project_id} was not found.",
        )
    return APIResponse(
        success=True,
        message="Project updated successfully.",
        data=project,
    )


@router.delete("/{project_id}", response_model=APIResponse[None])
async def delete_project(
    project_id: str,
    service: ProjectService = Depends(get_project_service),
):
    success = await service.delete_project(project_id)
    if not success:
        raise AppHTTPException(
            status_code=404,
            code="PROJECT_NOT_FOUND",
            message=f"Project {project_id} was not found.",
        )
    return APIResponse(
        success=True,
        message="Project deleted successfully.",
        data=None,
    )
