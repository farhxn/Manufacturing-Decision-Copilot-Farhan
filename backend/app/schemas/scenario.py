"""Scenario API schemas."""

from pydantic import BaseModel, Field

from app.schemas.supplier import SupplierScoreSchema


class ScenarioCreateRequest(BaseModel):
    project_id: str
    name: str = "Custom Scenario"
    description: str | None = None
    shipping_multiplier: float = 1.0
    currency_rate: float = 1.0
    demand_multiplier: float = 1.0
    lead_time_adjustment_days: int = 0
    disabled_supplier_ids: list[str] = Field(default_factory=list)


class ScenarioSummarySchema(BaseModel):
    id: str
    project_id: str
    name: str
    description: str | None = None
    shipping_multiplier: float
    currency_rate: float
    demand_multiplier: float
    lead_time_adjustment_days: int
    disabled_supplier_ids: list[str] = Field(default_factory=list)


class ScenarioRankingDeltaSchema(BaseModel):
    supplier_id: str
    supplier_name: str
    baseline_rank: int
    scenario_rank: int
    rank_changed: bool
    baseline_score: float
    scenario_score: float
    landed_cost: float
    scores: SupplierScoreSchema


class ScenarioSimulationSchema(BaseModel):
    scenario_id: str
    previous_top_supplier_id: str
    new_top_supplier_id: str
    ranking_changed: bool
    rankings: list[ScenarioRankingDeltaSchema] = Field(default_factory=list)
    # Phase 6: AI-generated explanation of the ranking change
    explanation: str | None = None
