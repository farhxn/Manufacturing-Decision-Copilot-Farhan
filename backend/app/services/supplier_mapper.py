"""Maps database supplier models to deterministic engine inputs."""

from __future__ import annotations

from dataclasses import dataclass, field

from app.engines.types import ScoreWeights, SupplierInput
from app.models.project import Project
from app.models.supplier import Supplier

RISK_CATEGORIES = ("financial", "country", "supply", "compliance", "capacity")
DEFAULT_REQUIRED_CERTS = ("ISO 9001",)
DEFAULT_REQUIRED_CAPABILITIES: tuple[str, ...] = ()

# Safety score used when a SupplierRiskScore row is missing for a category.
# Magnitude = 100 - 70 = 30  →  moderate penalty for missing data.
_DEFAULT_SAFETY_SCORE = 70.0


def project_to_weights(project: Project) -> ScoreWeights:
    return ScoreWeights(
        cost=project.cost_weight,
        quality=project.quality_weight,
        delivery=project.delivery_weight,
        risk=project.risk_weight,
        capability=project.capability_weight,
        compliance=project.compliance_weight,
    )


def _risk_magnitude(risk_scores: dict[str, float], category: str) -> float:
    safety_score = risk_scores.get(category, _DEFAULT_SAFETY_SCORE)
    return max(0.0, min(100.0, 100.0 - safety_score))


# ── Per-supplier risk metadata ────────────────────────────────────────────────

@dataclass
class RiskInputMeta:
    """
    Metadata that accompanies the five risk magnitudes fed into the engine.

    Kept separate from SupplierInput (frozen dataclass) to avoid changing
    the engine's data contract.  The service layer merges this with the
    SupplierScoreBreakdown to build the full RiskBreakdown.
    """
    supplier_id: str
    # "db" = row existed in supplier_risk_scores; "default" = row was missing
    data_sources: dict[str, str] = field(default_factory=dict)
    # Free-text details from SupplierRiskScore.details, keyed by category
    details: dict[str, str | None] = field(default_factory=dict)
    # ChromaDB chunk IDs — populated later by the RAG layer, empty here
    evidence_ids: dict[str, list[str]] = field(default_factory=dict)


def supplier_to_input(supplier: Supplier) -> SupplierInput:
    price = supplier.prices[0] if supplier.prices else None
    quoted_price = price.unit_price if price else supplier.unit_price
    shipping_cost = (
        price.shipping_cost if price
        else max(0.0, supplier.landed_cost - supplier.unit_price)
    )
    duty_rate = price.duty_rate if price else 0.0

    risk_scores = {item.category: item.score for item in supplier.risk_scores}
    overall = supplier.overall_score or 75.0

    return SupplierInput(
        supplier_id=supplier.id,
        quoted_price=quoted_price,
        shipping_cost=shipping_cost,
        duty_rate=duty_rate,
        lead_time_days=supplier.lead_time_days,
        defect_rate=max(0.0, min(100.0, (100.0 - overall) * 0.35)),
        inspection_pass_rate=max(0.0, min(100.0, overall * 0.95 + 5.0)),
        customer_rating=max(1.0, min(5.0, 1.0 + (overall / 100.0) * 4.0)),
        on_time_delivery_pct=max(
            0.0,
            min(100.0, 65.0 + max(0, 30 - supplier.lead_time_days) * 1.2),
        ),
        production_capacity_pct=max(0.0, min(100.0, overall)),
        engineering_support=any(
            "engineering" in cap.name.lower() for cap in supplier.capabilities
        ),
        capabilities=tuple(cap.name for cap in supplier.capabilities),
        supplier_certs=tuple(
            cert.name for cert in supplier.certifications if cert.is_valid
        ),
        financial_risk=_risk_magnitude(risk_scores, "financial"),
        country_risk=_risk_magnitude(risk_scores, "country"),
        supply_risk=_risk_magnitude(risk_scores, "supply"),
        compliance_risk=_risk_magnitude(risk_scores, "compliance"),
        capacity_risk=_risk_magnitude(risk_scores, "capacity"),
    )


def supplier_to_risk_meta(supplier: Supplier) -> RiskInputMeta:
    """
    Build the per-factor metadata that accompanies SupplierInput.

    Distinguishes which risk categories came from real DB rows ("db") versus
    the hardcoded default safety score of 70 ("default").
    Records the free-text details stored against each SupplierRiskScore row.
    """
    risk_row_map = {item.category: item for item in supplier.risk_scores}
    data_sources: dict[str, str] = {}
    details: dict[str, str | None] = {}

    for cat in RISK_CATEGORIES:
        if cat in risk_row_map:
            data_sources[cat] = "db"
            details[cat] = risk_row_map[cat].details or None
        else:
            data_sources[cat] = "default"
            details[cat] = (
                f"No {cat} risk data on record — scored using default safety "
                f"score of {_DEFAULT_SAFETY_SCORE:.0f}/100."
            )

    return RiskInputMeta(
        supplier_id=supplier.id,
        data_sources=data_sources,
        details=details,
        evidence_ids={cat: [] for cat in RISK_CATEGORIES},  # filled by RAG later
    )


def suppliers_to_inputs(suppliers: list[Supplier]) -> list[SupplierInput]:
    return [supplier_to_input(supplier) for supplier in suppliers]


def suppliers_to_risk_metas(suppliers: list[Supplier]) -> dict[str, RiskInputMeta]:
    """Return a dict keyed by supplier_id for fast lookup in the service."""
    return {supplier.id: supplier_to_risk_meta(supplier) for supplier in suppliers}
