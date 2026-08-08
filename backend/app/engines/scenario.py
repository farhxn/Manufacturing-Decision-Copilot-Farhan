"""
Manufacturing Decision Copilot - Scenario Engine
Pure Python deterministic scenario simulation.
"""

from app.engines.ranking import get_top_supplier_id, score_suppliers
from app.engines.types import (
    ScenarioConfig,
    ScenarioResult,
    ScoreWeights,
    SupplierInput,
)


def simulate_scenario(
    suppliers: list[SupplierInput],
    scenario_config: ScenarioConfig,
    weights: ScoreWeights | None = None,
    required_certs: list[str] | None = None,
    required_capabilities: list[str] | None = None,
) -> ScenarioResult:
    """
    Simulates a procurement scenario and compares rankings against baseline.

    Baseline uses default scenario settings (no multipliers or overrides).
    """
    baseline_ranking = score_suppliers(
        suppliers=suppliers,
        weights=weights,
        required_certs=required_certs,
        required_capabilities=required_capabilities,
        config=ScenarioConfig(),
    )
    scenario_ranking = score_suppliers(
        suppliers=suppliers,
        weights=weights,
        required_certs=required_certs,
        required_capabilities=required_capabilities,
        config=scenario_config,
    )

    previous_top = get_top_supplier_id(baseline_ranking)
    new_top = get_top_supplier_id(scenario_ranking)

    return ScenarioResult(
        baseline_ranking=tuple(baseline_ranking),
        scenario_ranking=tuple(scenario_ranking),
        previous_top_supplier_id=previous_top,
        new_top_supplier_id=new_top,
        ranking_changed=previous_top != new_top,
    )
