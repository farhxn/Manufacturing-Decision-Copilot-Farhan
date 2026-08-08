"""
Manufacturing Decision Copilot - Compliance Engine
Pure Python deterministic compliance calculations.
"""


def _cert_matches(held: str, req_lower: str) -> bool:
    """Return True when a held certification satisfies a required certification."""
    if held == req_lower:
        return True
    if held.startswith(req_lower + ":"):
        return True
    if " " in req_lower and held.startswith(req_lower + " "):
        return True
    if " " not in req_lower and held.startswith(req_lower + " "):
        suffix = held[len(req_lower) + 1 :]
        # Block broad family prefixes like "ISO" matching "ISO 9001:2015".
        if suffix and not suffix[0].isdigit():
            return True
    return False


def calculate_compliance_score(
    supplier_certs: list[str],
    required_certs: list[str]
) -> float:
    """
    Calculates the compliance score based on certifications.
    If a required certification is missing, the score is 0.
    Otherwise, it evaluates to 100.
    
    Args:
        supplier_certs: List of certification names the supplier holds (e.g., ["ISO 9001", "RoHS"]).
        required_certs: List of certification names that are mandatory.
        
    Returns:
        float: The compliance score (0.0 or 100.0)
    """
    if not required_certs:
        # If no certs are explicitly required, we assume full compliance
        return 100.0

    # Standardize casing for comparison
    supplier_certs_lower = [c.lower() for c in supplier_certs]

    for req in required_certs:
        req_lower = req.strip().lower()
        matched = any(
            _cert_matches(held, req_lower)
            for held in supplier_certs_lower
        )
        if not matched:
            return 0.0

    # All mandatory certifications are present
    return 100.0
