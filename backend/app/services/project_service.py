import uuid
from typing import List

from app.models.project import Project
from app.repositories.project_repository import ProjectRepository
from app.schemas.project import ProjectCreateSchema, ProjectUpdateSchema

class ProjectService:
    def __init__(self, project_repo: ProjectRepository):
        self.project_repo = project_repo

    async def list_projects(self, organization_id: str) -> List[Project]:
        return await self.project_repo.list_projects(organization_id)

    async def get_project(self, project_id: str) -> Project | None:
        return await self.project_repo.get_by_id(project_id)

    async def create_project(self, organization_id: str, data: ProjectCreateSchema) -> Project:
        project = Project(
            id=str(uuid.uuid4()),
            organization_id=organization_id,
            name=data.name,
            description=data.description,
            status=data.status or "active",
        )
        return await self.project_repo.create(project)

    async def update_project(self, project_id: str, data: ProjectUpdateSchema) -> Project | None:
        project = await self.project_repo.get_by_id(project_id)
        if not project:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(project, key, value)
            
        return await self.project_repo.update(project)

    async def delete_project(self, project_id: str) -> bool:
        project = await self.project_repo.get_by_id(project_id)
        if not project:
            return False
            
        return await self.project_repo.delete(project)
