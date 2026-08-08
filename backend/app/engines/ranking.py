"""
Manufacturing Decision Copilot - Ranking Engine
Pure Python deterministic supplier ranking.
"""

from app.engines.capability import calculate_capability_score
from app.engines.compliance import calculate_compliance_score
from app.engines.cost import calculate_cost_score, calculate_landed_cost
from app.engines.delivery import calculate_delivery_score
from app.engines.quality import calculate_quality_score
from app.engines.risk import calculate_risk_breakdown, calculate_risk_score
from app.engines.types import (
    ScenarioConfig,
    ScoreWeights,
    SupplierInput,
    SupplierScoreBreakdown,
)


def calculate_final_score(
    cost_score: float,
    quality_score: float,
    delivery_score: float,
    risk_score: float,
    capability_score: float,
    compliance_score: float,
    weights: ScoreWeights,
) -> float:
    """Calculates the weighted final score for a supplier."""
    final_score = (
        cost_score * weights.cost
        + quality_score * weights.quality
        + delivery_score * weights.delivery
        + risk_score * weights.risk
        + capability_score * weights.capability
        + compliance_score * weights.compliance
    )
    return max(0.0, min(100.0, round(final_score, 2)))


def _is_supplier_available(supplier: SupplierInput, config: ScenarioConfig) -> bool:
    if supplier.supplier_id not in config.supplier_availability:
        return True
    return config.supplier_availability[supplier.supplier_id]


def _effective_certs(supplier: SupplierInput, config: ScenarioConfig) -> list[str]:
    certs = list(supplier.supplier_certs)
    for cert_name, is_valid in config.certification_overrides.items():
        cert_lower = cert_name.lower()
        if not is_valid:
            certs = [cert for cert in certs if cert.lower() != cert_lower]
    return certs


def _adjusted_capacity_pct(supplier: SupplierInput, config: ScenarioConfig) -> float:
    if config.demand_multiplier <= 0:
        return 0.0
    adjusted = supplier.production_capacity_pct / config.demand_multiplier
    return max(0.0, min(100.0, adjusted))


def _compute_landed_cost(supplier: SupplierInput, config: ScenarioConfig) -> float:
    duty_rate = (
        config.import_duty_rate if config.import_duty_rate is not None else supplier.duty_rate
    )
    return calculate_landed_cost(
        quoted_price=supplier.quoted_price * config.material_cost_multiplier,
        shipping_cost=supplier.shipping_cost,
        duty_rate=duty_rate,
        insurance_cost=supplier.insurance_cost,
        taxes=supplier.taxes,
        shipping_multiplier=config.shipping_multiplier,
        currency_rate=config.currency_rate * supplier.currency_rate,
    )


def score_suppliers(
    suppliers: list[SupplierInput],
    weights: ScoreWeights | None = None,
    required_certs: list[str] | None = None,
    required_capabilities: list[str] | None = None,
    config: ScenarioConfig | None = None,
) -> list[SupplierScoreBreakdown]:
    """
    Scores and ranks suppliers using all deterministic engines.

    Returns suppliers sorted by final score descending. Disqualified suppliers
    receive zero scores and are ranked last.
    """
    if not suppliers:
        return []

    active_weights = weights or ScoreWeights()
    active_required_certs = required_certs or []
    active_required_capabilities = required_capabilities or []
    active_config = config or ScenarioConfig()

    active_suppliers = [
        supplier
        for supplier in suppliers
        if _is_supplier_available(supplier, active_config)
    ]

    landed_costs = {
        supplier.supplier_id: _compute_landed_cost(supplier, active_config)
        for supplier in active_suppliers
    }
    min_landed_cost = min(landed_costs.values()) if landed_costs else 0.0

    lead_times = [
        max(1, supplier.lead_time_days + active_config.lead_time_adjustment_days)
        for supplier in active_suppliers
    ]
    min_lead_time = min(lead_times) if lead_times else 1

    breakdowns: list[SupplierScoreBreakdown] = []

    for supplier in suppliers:
        if not _is_supplier_available(supplier, active_config):
            breakdowns.append(
                SupplierScoreBreakdown(
                    supplier_id=supplier.supplier_id,
                    landed_cost=0.0,
                    cost_score=0.0,
                    quality_score=0.0,
                    delivery_score=0.0,
                    risk_score=0.0,
                    capability_score=0.0,
                    compliance_score=0.0,
                    final_score=0.0,
                    disqualified=True,
                )
            )
            continue

        landed_cost = landed_costs[supplier.supplier_id]
        lead_time_days = max(1, supplier.lead_time_days + active_config.lead_time_adjustment_days)
        capacity_pct = _adjusted_capacity_pct(supplier, active_config)

        cost_score = calculate_cost_score(min_landed_cost, landed_cost)
        quality_score = calculate_quality_score(
            defect_rate=supplier.defect_rate,
            inspection_pass_rate=supplier.inspection_pass_rate,
            customer_rating=supplier.customer_rating,
        )
        delivery_score = calculate_delivery_score(
            lead_time_days=lead_time_days,
            min_lead_time_days=min_lead_time,
            on_time_delivery_pct=supplier.on_time_delivery_pct,
            production_capacity_pct=capacity_pct,
        )
        risk_score = calculate_risk_score(
            financial_risk=supplier.financial_risk,
            country_risk=supplier.country_risk,
            supply_risk=supplier.supply_risk,
            compliance_risk=supplier.compliance_risk,
            capacity_risk=supplier.capacity_risk,
        )
        # Build full breakdown — stored on the SupplierScoreBreakdown for
        # detail endpoints.  Uses data_sources/details from the input if
        # they were attached by the mapper.
        risk_breakdown = calculate_risk_breakdown(
            financial_risk=supplier.financial_risk,
            country_risk=supplier.country_risk,
            supply_risk=supplier.supply_risk,
            compliance_risk=supplier.compliance_risk,
            capacity_risk=supplier.capacity_risk,
            data_sources=getattr(supplier, "_risk_data_sources", None),
            details=getattr(supplier, "_risk_details", None),
            evidence_ids=getattr(supplier, "_risk_evidence_ids", None),
        )
        capability_score = calculate_capability_score(
            supplier_capabilities=list(supplier.capabilities),
            required_capabilities=active_required_capabilities,
            production_capacity_pct=capacity_pct,
            engineering_support=supplier.engineering_support,
        )
        compliance_score = calculate_compliance_score(
            supplier_certs=_effective_certs(supplier, active_config),
            required_certs=active_required_certs,
        )

        final_score = calculate_final_score(
            cost_score=cost_score,
            quality_score=quality_score,
            delivery_score=delivery_score,
            risk_score=risk_score,
            capability_score=capability_score,
            compliance_score=compliance_score,
            weights=active_weights,
        )

        breakdowns.append(
            SupplierScoreBreakdown(
                supplier_id=supplier.supplier_id,
                landed_cost=landed_cost,
                cost_score=cost_score,
                quality_score=quality_score,
                delivery_score=delivery_score,
                risk_score=risk_score,
                capability_score=capability_score,
                compliance_score=compliance_score,
                final_score=final_score,
                risk_breakdown=risk_breakdown,
            )
        )

    ranked = sorted(
        breakdowns,
        key=lambda item: (-item.final_score, item.supplier_id),
    )
    return [
        SupplierScoreBreakdown(
            supplier_id=item.supplier_id,
            landed_cost=item.landed_cost,
            cost_score=item.cost_score,
            quality_score=item.quality_score,
            delivery_score=item.delivery_score,
            risk_score=item.risk_score,
            capability_score=item.capability_score,
            compliance_score=item.compliance_score,
            final_score=item.final_score,
            rank=index,
            disqualified=item.disqualified,
            risk_breakdown=item.risk_breakdown,
        )
        for index, item in enumerate(ranked, start=1)
    ]


def get_top_supplier_id(ranking: list[SupplierScoreBreakdown]) -> str:
    """Returns the supplier_id of the top-ranked active supplier."""
    for item in ranking:
        if not item.disqualified:
            return item.supplier_id
    return ""
