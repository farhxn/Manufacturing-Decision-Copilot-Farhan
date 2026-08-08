"""Shared FastAPI dependencies and service wiring."""

from collections.abc import AsyncGenerator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.repositories.document_repository import DocumentRepository
from app.repositories.evidence_repository import EvidenceRepository
from app.repositories.project_repository import ProjectRepository
from app.repositories.recommendation_repository import RecommendationRepository
from app.repositories.report_repository import ReportRepository
from app.repositories.scenario_repository import ScenarioRepository
from app.repositories.supplier_repository import SupplierRepository
from app.services.dashboard_service import DashboardService
from app.services.document_service import DocumentService
from app.services.evidence_service import EvidenceService
from app.services.project_service import ProjectService
from app.services.recommendation_service import RecommendationService
from app.services.report_service import ReportService
from app.services.scenario_service import ScenarioService
from app.services.supplier_service import SupplierService


async def get_project_service(
    session: AsyncSession = Depends(get_db),
) -> AsyncGenerator[ProjectService, None]:
    yield ProjectService(ProjectRepository(session))

async def get_document_service(
    session: AsyncSession = Depends(get_db),
) -> AsyncGenerator[DocumentService, None]:
    yield DocumentService(DocumentRepository(session))


async def get_supplier_service(
    session: AsyncSession = Depends(get_db),
) -> AsyncGenerator[SupplierService, None]:
    yield SupplierService(SupplierRepository(session), ProjectRepository(session))


async def get_recommendation_service(
    session: AsyncSession = Depends(get_db),
) -> AsyncGenerator[RecommendationService, None]:
    yield RecommendationService(
        SupplierRepository(session),
        ProjectRepository(session),
        RecommendationRepository(session),
        EvidenceRepository(session),   # Phase 6: evidence persistence
        DocumentRepository(session),
    )


async def get_scenario_service(
    session: AsyncSession = Depends(get_db),
) -> AsyncGenerator[ScenarioService, None]:
    yield ScenarioService(
        ScenarioRepository(session),
        SupplierRepository(session),
        ProjectRepository(session),
    )


async def get_dashboard_service(
    session: AsyncSession = Depends(get_db),
) -> AsyncGenerator[DashboardService, None]:
    supplier_service = SupplierService(SupplierRepository(session), ProjectRepository(session))
    recommendation_service = RecommendationService(
        SupplierRepository(session),
        ProjectRepository(session),
        RecommendationRepository(session),
        EvidenceRepository(session),   # Phase 6
        DocumentRepository(session),
    )
    yield DashboardService(
        ProjectRepository(session),
        supplier_service,
        recommendation_service,
    )


async def get_evidence_service(
    session: AsyncSession = Depends(get_db),
) -> AsyncGenerator[EvidenceService, None]:
    yield EvidenceService(EvidenceRepository(session))


async def get_report_service(
    session: AsyncSession = Depends(get_db),
) -> AsyncGenerator[ReportService, None]:
    recommendation_service = RecommendationService(
        SupplierRepository(session),
        ProjectRepository(session),
        RecommendationRepository(session),
        EvidenceRepository(session),
        DocumentRepository(session),
    )
    yield ReportService(
        ReportRepository(session),
        ProjectRepository(session),
        recommendation_service,
    )
