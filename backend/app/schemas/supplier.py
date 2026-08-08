"""Supplier API schemas."""

from pydantic import BaseModel, Field


# ── Shared sub-schemas ────────────────────────────────────────────────────────

class SupplierCreateSchema(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    country: str = Field(..., min_length=2, max_length=100)
    city: str | None = Field(None, max_length=100)
    status: str = Field(default="Active")
    unit_price: float = Field(..., ge=0)
    landed_cost: float = Field(..., ge=0)
    currency: str = Field(default="USD", max_length=10)
    lead_time_days: int = Field(..., ge=0)
    moq: int = Field(..., ge=0)
    risk_level: str = Field(default="Medium")
    project_id: str | None = None

class SupplierUpdateSchema(BaseModel):
    name: str | None = Field(None, min_length=2, max_length=255)
    country: str | None = Field(None, min_length=2, max_length=100)
    city: str | None = Field(None, max_length=100)
    status: str | None = None
    unit_price: float | None = Field(None, ge=0)
    landed_cost: float | None = Field(None, ge=0)
    currency: str | None = Field(None, max_length=10)
    lead_time_days: int | None = Field(None, ge=0)
    moq: int | None = Field(None, ge=0)
    risk_level: str | None = None



class SupplierCapabilitySchema(BaseModel):
    name: str
    category: str
    verified: bool = True


class SupplierCertificationSchema(BaseModel):
    name: str
    issuer: str | None = None
    is_valid: bool = True


class SupplierScoreSchema(BaseModel):
    cost_score: float
    quality_score: float
    delivery_score: float
    risk_score: float
    capability_score: float
    compliance_score: float
    final_score: float
    rank: int | None = None
    landed_cost: float


# ── Explainable risk schemas ──────────────────────────────────────────────────

class RiskFactorSchema(BaseModel):
    """
    One dimension of the deterministic risk score, fully auditable.

    score                : 0–100 safety score (higher = safer)
    magnitude            : 100 - score (the raw risk input to the formula)
    weight               : formula weight (e.g. 0.25 for financial risk)
    weighted_contribution: magnitude × weight — this is what is subtracted from 100
    data_source          : "db" — from a real SupplierRiskScore row
                           "default" — inferred (no row stored)
    status               : "Low Risk" | "Moderate Risk" | "Elevated Risk" | "High Risk"
    confidence           : 1.0 if data_source == "db", 0.5 if "default"
    details              : free-text from SupplierRiskScore.details or a
                           description of why the default was used
    evidence_ids         : ChromaDB chunk IDs supporting this factor
    """
    factor_id: str
    name: str
    score: float
    magnitude: float
    weight: float
    weighted_contribution: float
    data_source: str
    status: str
    confidence: float
    details: str | None = None
    evidence_ids: list[str] = Field(default_factory=list)


class RiskBreakdownSchema(BaseModel):
    """
    Fully auditable risk score profile.

    The overall_score is reproducible:
        overall_score = 100 - sum(f.weighted_contribution for f in factors)
        clamped to [0, 100], rounded to 2 dp.
    """
    overall_score: float
    risk_level: str               # "Low" | "Moderate" | "Elevated" | "High"
    factors: list[RiskFactorSchema]
    primary_driver_id: str        # factor_id with highest weighted_contribution
    primary_driver_name: str
    total_weighted_risk: float
    calculation_version: str
    evidence_coverage: float      # 0.0–1.0 fraction of factors with evidence


# ── Supplier response schemas ─────────────────────────────────────────────────

class SupplierSummarySchema(BaseModel):
    id: str
    name: str
    country: str
    city: str | None = None
    status: str
    unit_price: float
    landed_cost: float
    currency: str
    lead_time_days: int
    moq: int
    risk_level: str
    scores: SupplierScoreSchema


class SupplierDetailSchema(SupplierSummarySchema):
    capabilities: list[SupplierCapabilitySchema] = Field(default_factory=list)
    certifications: list[SupplierCertificationSchema] = Field(default_factory=list)
    # Full explainable risk profile — only on detail endpoint, not list
    risk_breakdown: RiskBreakdownSchema | None = None


class SupplierCompareRequest(BaseModel):
    supplier_ids: list[str] = Field(min_length=2, max_length=5)
    project_id: str | None = None
