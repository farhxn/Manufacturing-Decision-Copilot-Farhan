"""
Manufacturing Decision Copilot - Delivery Engine
Pure Python deterministic delivery calculations.
"""


def calculate_delivery_score(
    lead_time_days: int,
    min_lead_time_days: int,
    on_time_delivery_pct: float,
    production_capacity_pct: float = 100.0,
) -> float:
    """
    Calculates a normalized delivery score (0-100).

    Args:
        lead_time_days: Supplier lead time in days.
        min_lead_time_days: Shortest lead time across active suppliers.
        on_time_delivery_pct: Historical on-time delivery percentage.
        production_capacity_pct: Available production capacity percentage.

    Returns:
        float: Normalized delivery score between 0 and 100.
    """
    if lead_time_days <= 0 or min_lead_time_days <= 0:
        lead_time_component = 0.0
    else:
        lead_time_component = (min_lead_time_days / lead_time_days) * 100.0

    on_time_component = max(0.0, min(100.0, on_time_delivery_pct))
    capacity_component = max(0.0, min(100.0, production_capacity_pct))

    score = (
        lead_time_component * 0.45
        + on_time_component * 0.35
        + capacity_component * 0.20
    )
    return max(0.0, min(100.0, round(score, 2)))
