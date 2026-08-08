"""
Shared types for deterministic scoring engines.
"""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class SupplierInput:
    """Normalized supplier inputs for engine calculations."""

    supplier_id: str
    quoted_price: float
    shipping_cost: float
    duty_rate: float = 0.0
    insurance_cost: float = 0.0
    taxes: float = 0.0
    currency_rate: float = 1.0
    lead_time_days: int = 14
    defect_rate: float = 0.0
    inspection_pass_rate: float = 100.0
    customer_rating: float = 5.0
    on_time_delivery_pct: float = 100.0
    production_capacity_pct: float = 100.0
    engineering_support: bool = False
    capabilities: tuple[str, ...] = ()
    supplier_certs: tuple[str, ...] = ()
    financial_risk: float = 0.0
    country_risk: float = 0.0
    supply_risk: float = 0.0
    compliance_risk: float = 0.0
    capacity_risk: float = 0.0


@dataclass(frozen=True)
class ScoreWeights:
    cost: float = 0.30
    quality: float = 0.20
    delivery: float = 0.15
    risk: float = 0.15
    capability: float = 0.10
    compliance: float = 0.10


@dataclass(frozen=True)
class ScenarioConfig:
    shipping_multiplier: float = 1.0
    currency_rate: float = 1.0
    demand_multiplier: float = 1.0
    lead_time_adjustment_days: int = 0
    supplier_availability: dict[str, bool] = field(default_factory=dict)
    certification_overrides: dict[str, bool] = field(default_factory=dict)
    material_cost_multiplier: float = 1.0
    import_duty_rate: float | None = None


# ── Risk breakdown types ───────────────────────────────────────────────────────

@dataclass(frozen=True)
class RiskFactorDetail:
    """
    One dimension of the risk score, fully auditable.

    score             : 0–100 safety score for this factor (higher = safer)
    magnitude         : 100 - score  (the raw risk input to the formula)
    weight            : the formula weight (e.g. 0.25 for financial risk)
    weighted_contribution : magnitude × weight  (subtracts from 100 to get the overall score)
    safety_score_source : the stored SupplierRiskScore.score before inversion
    data_source       : "db" | "default"  — "default" means the row was missing
    details           : free-text details from SupplierRiskScore.details, if any
    evidence_ids      : ChromaDB chunk IDs relevant to this factor (from RAG retrieval)
    """
    factor_id: str          # "financial" | "country" | "supply" | "compliance" | "capacity"
    name: str               # Human-readable: "Financial Stability"
    score: float            # 0–100 safety score (higher = safer)
    magnitude: float        # 100 - score  (risk magnitude fed into formula)
    weight: float           # formula weight (e.g. 0.25)
    weighted_contribution: float  # magnitude × weight → subtracted from 100
    data_source: str        # "db" | "default"
    details: str | None = None
    evidence_ids: list[str] = field(default_factory=list)

    @property
    def status(self) -> str:
        """Descriptive status label for the factor."""
        if self.score >= 80:
            return "Low Risk"
        if self.score >= 60:
            return "Moderate Risk"
        if self.score >= 40:
            return "Elevated Risk"
        return "High Risk"

    @property
    def confidence(self) -> float:
        """Evidence confidence: 1.0 if from DB, 0.5 if default/inferred."""
        return 1.0 if self.data_source == "db" else 0.5


@dataclass(frozen=True)
class RiskBreakdown:
    """
    Fully auditable risk score breakdown.

    The overall_score is reproducible:
        overall_score = 100 - sum(f.weighted_contribution for f in factors)
        clamped to [0, 100], rounded to 2dp.

    primary_driver_id : factor_id of the factor contributing most to total risk
                        (i.e. highest weighted_contribution)
    calculation_version : bumped any time the formula changes
    evidence_coverage  : fraction of factors that have at least one evidence_id
    """
    overall_score: float
    risk_level: str          # "Low" | "Moderate" | "Elevated" | "High"
    factors: tuple[RiskFactorDetail, ...]
    primary_driver_id: str   # factor_id with highest weighted_contribution
    primary_driver_name: str
    total_weighted_risk: float   # sum of all weighted_contributions
    calculation_version: str = "v1"
    evidence_coverage: float = 0.0   # 0.0 – 1.0

    @property
    def primary_driver(self) -> RiskFactorDetail | None:
        for f in self.factors:
            if f.factor_id == self.primary_driver_id:
                return f
        return None


# ── Score breakdown types ──────────────────────────────────────────────────────

@dataclass(frozen=True)
class SupplierScoreBreakdown:
    supplier_id: str
    landed_cost: float
    cost_score: float
    quality_score: float
    delivery_score: float
    risk_score: float
    capability_score: float
    compliance_score: float
    final_score: float
    rank: int = 0
    disqualified: bool = False
    # Optional full risk breakdown — populated only when requested
    risk_breakdown: RiskBreakdown | None = None


@dataclass(frozen=True)
class ScenarioResult:
    baseline_ranking: tuple[SupplierScoreBreakdown, ...]
    scenario_ranking: tuple[SupplierScoreBreakdown, ...]
    previous_top_supplier_id: str
    new_top_supplier_id: str
    ranking_changed: bool
