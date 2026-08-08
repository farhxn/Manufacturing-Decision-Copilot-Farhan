"""
Manufacturing Decision Copilot - Risk Engine
Pure Python deterministic risk calculations.

The overall risk score is:
    score = 100 - (financial_risk × 0.25
                 + country_risk   × 0.20
                 + supply_risk    × 0.20
                 + compliance_risk × 0.20
                 + capacity_risk  × 0.15)
    clamped to [0, 100], rounded to 2 dp.

Inputs are *risk magnitudes* (0–100, higher = riskier).
The DB stores *safety scores* (0–100, higher = safer).
The mapper inverts them: magnitude = 100 - safety_score.

Two public functions are provided:
  calculate_risk_score()   — returns just the aggregate float (backward compatible)
  calculate_risk_breakdown() — returns a fully auditable RiskBreakdown object
"""

from __future__ import annotations

from app.engines.types import RiskBreakdown, RiskFactorDetail

# ── Formula constants — NEVER change without bumping CALCULATION_VERSION ───────

_WEIGHTS: dict[str, float] = {
    "financial":  0.25,
    "country":    0.20,
    "supply":     0.20,
    "compliance": 0.20,
    "capacity":   0.15,
}

_NAMES: dict[str, str] = {
    "financial":  "Financial Stability",
    "country":    "Country & Geopolitical Risk",
    "supply":     "Supply Chain Reliability",
    "compliance": "Regulatory Compliance Risk",
    "capacity":   "Operational Capacity Risk",
}

CALCULATION_VERSION = "v1"


# ── Internal helpers ───────────────────────────────────────────────────────────

def _risk_level(score: float) -> str:
    if score >= 80:
        return "Low"
    if score >= 60:
        return "Moderate"
    if score >= 40:
        return "Elevated"
    return "High"


def _build_factor(
    factor_id: str,
    magnitude: float,
    data_source: str,
    details: str | None,
    evidence_ids: list[str],
) -> RiskFactorDetail:
    weight = _WEIGHTS[factor_id]
    safety_score = round(100.0 - magnitude, 2)
    wc = round(magnitude * weight, 4)
    return RiskFactorDetail(
        factor_id=factor_id,
        name=_NAMES[factor_id],
        score=safety_score,
        magnitude=round(magnitude, 4),
        weight=weight,
        weighted_contribution=wc,
        data_source=data_source,
        details=details,
        evidence_ids=evidence_ids,
    )


# ── Public API ─────────────────────────────────────────────────────────────────

def calculate_risk_score(
    financial_risk: float,
    country_risk: float,
    supply_risk: float,
    compliance_risk: float,
    capacity_risk: float,
) -> float:
    """
    Backward-compatible single-value entry point.

    Inputs are risk magnitudes (0–100, higher = riskier).
    Returns a safety score (0–100, higher = safer).
    """
    total_risk = (
        financial_risk  * _WEIGHTS["financial"]  +
        country_risk    * _WEIGHTS["country"]    +
        supply_risk     * _WEIGHTS["supply"]     +
        compliance_risk * _WEIGHTS["compliance"] +
        capacity_risk   * _WEIGHTS["capacity"]
    )
    return max(0.0, min(100.0, round(100.0 - total_risk, 2)))


def calculate_risk_breakdown(
    financial_risk: float,
    country_risk: float,
    supply_risk: float,
    compliance_risk: float,
    capacity_risk: float,
    *,
    data_sources: dict[str, str] | None = None,
    details: dict[str, str | None] | None = None,
    evidence_ids: dict[str, list[str]] | None = None,
) -> RiskBreakdown:
    """
    Full auditable risk breakdown.

    Parameters
    ----------
    financial_risk, country_risk, supply_risk, compliance_risk, capacity_risk:
        Risk magnitudes (0–100, higher = riskier).  Same semantics as
        ``calculate_risk_score``.

    data_sources : dict mapping factor_id → "db" | "default"
        Indicates whether each factor came from a real DB row or was inferred
        from the default safety score of 70.

    details : dict mapping factor_id → free-text explanation from DB or None.

    evidence_ids : dict mapping factor_id → list of ChromaDB chunk IDs that
        support this factor.

    Returns
    -------
    RiskBreakdown with full per-factor detail and a reproducible overall_score.
    The overall_score == calculate_risk_score(...) for the same inputs.
    """
    _ds = data_sources or {}
    _det = details or {}
    _ev = evidence_ids or {}

    magnitudes = {
        "financial":  financial_risk,
        "country":    country_risk,
        "supply":     supply_risk,
        "compliance": compliance_risk,
        "capacity":   capacity_risk,
    }

    factors = tuple(
        _build_factor(
            factor_id=fid,
            magnitude=magnitudes[fid],
            data_source=_ds.get(fid, "db"),
            details=_det.get(fid),
            evidence_ids=_ev.get(fid, []),
        )
        for fid in _WEIGHTS
    )

    total_wc = sum(f.weighted_contribution for f in factors)
    overall = max(0.0, min(100.0, round(100.0 - total_wc, 2)))

    # Primary driver = factor with highest weighted_contribution
    primary = max(factors, key=lambda f: f.weighted_contribution)

    # Evidence coverage = fraction of factors that have at least one evidence_id
    with_evidence = sum(1 for f in factors if f.evidence_ids)
    evidence_coverage = round(with_evidence / len(factors), 4)

    return RiskBreakdown(
        overall_score=overall,
        risk_level=_risk_level(overall),
        factors=factors,
        primary_driver_id=primary.factor_id,
        primary_driver_name=primary.name,
        total_weighted_risk=round(total_wc, 4),
        calculation_version=CALCULATION_VERSION,
        evidence_coverage=evidence_coverage,
    )
