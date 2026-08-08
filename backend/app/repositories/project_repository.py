"""Project repository."""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import Document
from app.models.project import Project


class ProjectRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, project_id: str) -> Project | None:
        result = await self.session.execute(
            select(Project).where(Project.id == project_id)
        )
        return result.scalar_one_or_none()

    async def count_documents(self, project_id: str) -> int:
        result = await self.session.execute(
            select(func.count(Document.id)).where(Document.project_id == project_id)
        )
        return int(result.scalar_one())

    async def list_projects(self, organization_id: str) -> list[Project]:
        result = await self.session.execute(
            select(Project).where(Project.organization_id == organization_id).order_by(Project.created_at.desc())
        )
        return list(result.scalars().all())
        
    async def create(self, project: Project) -> Project:
        self.session.add(project)
        await self.session.commit()
        await self.session.refresh(project)
        return project
        
    async def update(self, project: Project) -> Project:
        await self.session.commit()
        await self.session.refresh(project)
        return project
        
    async def delete(self, project: Project) -> bool:
        await self.session.delete(project)
        await self.session.commit()
        return True

