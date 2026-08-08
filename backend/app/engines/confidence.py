"""
Manufacturing Decision Copilot - Confidence Engine
Pure Python deterministic confidence calculations.
"""


def calculate_confidence(
    extraction_quality: float,
    evidence_coverage: float,
    retrieval_quality: float,
    rule_agreement: float,
    data_completeness: float,
) -> float:
    """
    Calculates recommendation confidence (0.0-1.0).

    All inputs are expected on a 0.0-1.0 scale and are clamped before
    the weighted formula is applied.
    """
    eq = max(0.0, min(1.0, extraction_quality))
    ec = max(0.0, min(1.0, evidence_coverage))
    rq = max(0.0, min(1.0, retrieval_quality))
    ra = max(0.0, min(1.0, rule_agreement))
    dc = max(0.0, min(1.0, data_completeness))

    confidence = (
        eq * 0.30
        + ec * 0.20
        + rq * 0.20
        + ra * 0.20
        + dc * 0.10
    )
    return round(confidence, 4)


def confidence_label(confidence: float) -> str:
    """Maps a confidence ratio to a human-readable label."""
    if confidence >= 0.80:
        return "High"
    if confidence >= 0.60:
        return "Medium"
    return "Low"


def confidence_percentage(confidence: float) -> float:
    """Converts confidence ratio to a percentage for display."""
    return round(max(0.0, min(100.0, confidence * 100.0)), 1)
