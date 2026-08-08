"""Dashboard API schemas."""

from pydantic import BaseModel, Field

from app.schemas.recommendation import RecommendationSchema


class DashboardKPISchema(BaseModel):
    supplier_count: int
    document_count: int
    average_confidence: float
    top_supplier_score: float


class DashboardSchema(BaseModel):
    project_id: str
    project_name: str
    kpis: DashboardKPISchema
    recommendation: RecommendationSchema
