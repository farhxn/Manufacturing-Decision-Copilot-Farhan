"""
Manufacturing Decision Copilot - Capability Engine
Pure Python deterministic capability calculations.
"""


def calculate_capability_score(
    supplier_capabilities: list[str],
    required_capabilities: list[str],
    production_capacity_pct: float = 100.0,
    engineering_support: bool = False,
) -> float:
    """
    Calculates a normalized capability score (0-100).

    Args:
        supplier_capabilities: Capabilities the supplier offers.
        required_capabilities: Capabilities required for the project.
        production_capacity_pct: Available production capacity percentage.
        engineering_support: Whether supplier provides engineering support.

    Returns:
        float: Normalized capability score between 0 and 100.
    """
    if not required_capabilities:
        match_score = 100.0
    else:
        supplier_lower = [capability.lower() for capability in supplier_capabilities]
        matched = sum(
            1 for required in required_capabilities if required.lower() in supplier_lower
        )
        match_score = (matched / len(required_capabilities)) * 100.0

    capacity_component = max(0.0, min(100.0, production_capacity_pct))
    support_bonus = 10.0 if engineering_support else 0.0

    score = match_score * 0.70 + capacity_component * 0.30 + support_bonus
    return max(0.0, min(100.0, round(score, 2)))
