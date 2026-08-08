"""
Manufacturing Decision Copilot - Quality Engine
Pure Python deterministic quality calculations.
"""


def calculate_quality_score(
    defect_rate: float,
    inspection_pass_rate: float,
    customer_rating: float,
) -> float:
    """
    Calculates a normalized quality score (0-100).

    Args:
        defect_rate: Defect rate magnitude 0-100 (lower is better).
        inspection_pass_rate: Inspection pass rate 0-100 (higher is better).
        customer_rating: Customer rating on a 1-5 scale.

    Returns:
        float: Normalized quality score between 0 and 100.
    """
    defect_component = 100.0 - max(0.0, min(100.0, defect_rate))
    inspection_component = max(0.0, min(100.0, inspection_pass_rate))
    rating_component = max(0.0, min(100.0, ((customer_rating - 1.0) / 4.0) * 100.0))

    score = (
        defect_component * 0.40
        + inspection_component * 0.35
        + rating_component * 0.25
    )
    return max(0.0, min(100.0, round(score, 2)))
