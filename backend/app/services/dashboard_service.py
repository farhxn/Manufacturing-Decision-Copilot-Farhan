"""Dashboard business service."""

from app.repositories.project_repository import ProjectRepository
from app.schemas.dashboard import DashboardKPISchema, DashboardSchema
from app.services.recommendation_service import RecommendationService
from app.services.supplier_service import SupplierService


class DashboardService:
    def __init__(
        self,
        project_repo: ProjectRepository,
        supplier_service: SupplierService,
        recommendation_service: RecommendationService,
    ):
        self.project_repo = project_repo
        self.supplier_service = supplier_service
        self.recommendation_service = recommendation_service

    async def get_dashboard(self, project_id: str) -> DashboardSchema | None:
        project = await self.project_repo.get_by_id(project_id)
        if not project:
            return None

        suppliers, meta = await self.supplier_service.list_suppliers(project_id, limit=500)
        recommendation = await self.recommendation_service.get_recommendation(project_id)
        if not recommendation:
            return None

        document_count = await self.project_repo.count_documents(project_id)
        top_score = suppliers[0].scores.final_score if suppliers else 0.0

        return DashboardSchema(
            project_id=project.id,
            project_name=project.name,
            kpis=DashboardKPISchema(
                supplier_count=meta.total,
                document_count=document_count,
                average_confidence=recommendation.confidence_score,
                top_supplier_score=top_score,
            ),
            recommendation=recommendation,
        )
