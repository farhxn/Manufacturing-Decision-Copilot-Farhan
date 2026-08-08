"""
Manufacturing Decision Copilot - Cost Engine
Pure Python deterministic cost calculations.
"""

def calculate_landed_cost(
    quoted_price: float,
    shipping_cost: float,
    duty_rate: float,
    insurance_cost: float = 0.0,
    taxes: float = 0.0,
    shipping_multiplier: float = 1.0,
    currency_rate: float = 1.0
) -> float:
    """
    Calculates the total landed cost for a unit.
    
    Args:
        quoted_price: Base unit price
        shipping_cost: Base shipping cost
        duty_rate: Duty rate as a decimal (e.g., 0.05 for 5%)
        insurance_cost: Insurance cost
        taxes: Any additional taxes
        shipping_multiplier: Multiplier for scenario simulation (default 1.0)
        currency_rate: Currency conversion rate to base currency (default 1.0)
        
    Returns:
        float: The calculated landed cost
    """
    duty_amount = quoted_price * duty_rate
    base_cost = quoted_price + (shipping_cost * shipping_multiplier) + duty_amount + insurance_cost + taxes
    return round(base_cost * currency_rate, 2)


def calculate_cost_score(min_landed_cost: float, supplier_landed_cost: float) -> float:
    """
    Calculates the normalized cost score (0-100).
    The supplier with the minimum landed cost gets 100.
    
    Args:
        min_landed_cost: The lowest landed cost across all active suppliers
        supplier_landed_cost: The landed cost of the supplier being scored
        
    Returns:
        float: Normalized score between 0 and 100
    """
    if supplier_landed_cost <= 0:
        return 0.0
    
    # Using the formula: (min_landed_cost / supplier_landed_cost) * 100
    score = (min_landed_cost / supplier_landed_cost) * 100.0
    return max(0.0, min(100.0, round(score, 2)))
