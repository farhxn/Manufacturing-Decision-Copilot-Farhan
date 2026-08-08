"""
Manufacturing Decision Copilot - API v1 Router
"""
from fastapi import APIRouter

from app.api.v1 import dashboard, documents, evidence, health, projects, recommendations, reports, scenarios, suppliers

router = APIRouter(prefix="/api/v1")

router.include_router(health.router)
router.include_router(projects.router)
router.include_router(documents.router)
router.include_router(suppliers.router)
router.include_router(recommendations.router)
router.include_router(scenarios.router)
router.include_router(dashboard.router)
router.include_router(evidence.router)
router.include_router(reports.router)
