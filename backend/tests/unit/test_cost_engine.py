import pytest
from app.engines.cost import calculate_landed_cost, calculate_cost_score


# ── calculate_landed_cost ────────────────────────────────────────────────────

def test_landed_cost_basic():
    # quoted_price=100, shipping=10, duty=5% of 100=5 → 115
    cost = calculate_landed_cost(
        quoted_price=100.0,
        shipping_cost=10.0,
        duty_rate=0.05,
    )
    assert cost == 115.0


def test_landed_cost_with_insurance_and_taxes():
    # 100 + 10 + 5 (duty) + 2 (insurance) + 3 (taxes) = 120
    cost = calculate_landed_cost(
        quoted_price=100.0,
        shipping_cost=10.0,
        duty_rate=0.05,
        insurance_cost=2.0,
        taxes=3.0,
    )
    assert cost == 120.0


def test_landed_cost_with_shipping_multiplier():
    # shipping*1.4 = 14; 100 + 14 + 5 (duty) = 119
    cost = calculate_landed_cost(
        quoted_price=100.0,
        shipping_cost=10.0,
        duty_rate=0.05,
        shipping_multiplier=1.4,
    )
    assert cost == 119.0


def test_landed_cost_with_currency_conversion():
    # (100 + 10 + 5) * 1.2 = 115 * 1.2 = 138.0
    cost = calculate_landed_cost(
        quoted_price=100.0,
        shipping_cost=10.0,
        duty_rate=0.05,
        currency_rate=1.2,
    )
    assert cost == 138.0


def test_landed_cost_zero_duty():
    # No duty: 200 + 25 + 0 = 225
    cost = calculate_landed_cost(
        quoted_price=200.0,
        shipping_cost=25.0,
        duty_rate=0.0,
    )
    assert cost == 225.0


def test_landed_cost_high_duty_rate():
    # 50% duty: 100 + 10 + 50 = 160
    cost = calculate_landed_cost(
        quoted_price=100.0,
        shipping_cost=10.0,
        duty_rate=0.50,
    )
    assert cost == 160.0


def test_landed_cost_all_components():
    # Full combination: quoted=200, shipping=30, duty=10%(=20), insurance=5,
    # taxes=8, shipping_multiplier=1.2, currency_rate=1.1
    # shipping_adjusted = 30 * 1.2 = 36
    # base = 200 + 36 + 20 + 5 + 8 = 269
    # landed = 269 * 1.1 = 295.9
    cost = calculate_landed_cost(
        quoted_price=200.0,
        shipping_cost=30.0,
        duty_rate=0.10,
        insurance_cost=5.0,
        taxes=8.0,
        shipping_multiplier=1.2,
        currency_rate=1.1,
    )
    assert cost == 295.9


def test_landed_cost_shipping_multiplier_only_affects_shipping():
    # shipping_multiplier changes shipping but NOT quoted_price or duty.
    # quoted=100, shipping=20*1.5=30, duty=5%(100)=5 → 135
    cost = calculate_landed_cost(
        quoted_price=100.0,
        shipping_cost=20.0,
        duty_rate=0.05,
        shipping_multiplier=1.5,
    )
    assert cost == 135.0


def test_landed_cost_currency_applies_to_total():
    # currency_rate wraps the entire landed cost.
    # base = 50 + 10 + 5 = 65; landed = 65 * 2.0 = 130.0
    cost = calculate_landed_cost(
        quoted_price=50.0,
        shipping_cost=10.0,
        duty_rate=0.10,
        currency_rate=2.0,
    )
    assert cost == 130.0


def test_landed_cost_zero_shipping():
    # No shipping cost: 80 + 0 + 4 = 84
    cost = calculate_landed_cost(
        quoted_price=80.0,
        shipping_cost=0.0,
        duty_rate=0.05,
    )
    assert cost == 84.0


def test_landed_cost_precision_rounding():
    # Result rounded to 2 decimal places.
    # 99.99 + 9.99 + 4.9995(≈5.00) = 114.9795 → 114.98
    cost = calculate_landed_cost(
        quoted_price=99.99,
        shipping_cost=9.99,
        duty_rate=0.05,
    )
    assert cost == round(99.99 + 9.99 + 99.99 * 0.05, 2)


def test_landed_cost_all_zero():
    # All zero inputs: result is 0
    cost = calculate_landed_cost(
        quoted_price=0.0,
        shipping_cost=0.0,
        duty_rate=0.0,
    )
    assert cost == 0.0


# ── calculate_cost_score ─────────────────────────────────────────────────────

def test_cost_score_best_supplier():
    # Supplier with minimum cost → score 100
    score = calculate_cost_score(min_landed_cost=100.0, supplier_landed_cost=100.0)
    assert score == 100.0


def test_cost_score_worse_supplier():
    # Double the minimum cost → score 50
    score = calculate_cost_score(min_landed_cost=100.0, supplier_landed_cost=200.0)
    assert score == 50.0


def test_cost_score_zero_cost():
    # Supplier landed cost of 0 → score 0 (guards division by zero)
    score = calculate_cost_score(min_landed_cost=100.0, supplier_landed_cost=0.0)
    assert score == 0.0


def test_cost_score_negative_cost():
    # Negative landed cost → score 0
    score = calculate_cost_score(min_landed_cost=100.0, supplier_landed_cost=-10.0)
    assert score == 0.0


def test_cost_score_10_percent_more_expensive():
    # 10% more than minimum: min=100, supplier=110 → 100/110*100 ≈ 90.91
    score = calculate_cost_score(min_landed_cost=100.0, supplier_landed_cost=110.0)
    assert score == round(100.0 / 110.0 * 100.0, 2)


def test_cost_score_capped_at_100():
    # If supplier is somehow cheaper than min (shouldn't happen), cap at 100
    score = calculate_cost_score(min_landed_cost=200.0, supplier_landed_cost=100.0)
    assert score == 100.0


def test_cost_score_zero_min_landed_cost():
    # If min_landed_cost is 0 the formula divides by supplier cost; 0/anything = 0
    # Guard: score should be 0 rather than divide-by-zero
    score = calculate_cost_score(min_landed_cost=0.0, supplier_landed_cost=100.0)
    assert score == 0.0


def test_cost_score_realistic_three_supplier_comparison():
    # Three suppliers: cheapest, middle, most expensive
    cheapest_landed = 115.0
    middle_landed = 132.0
    expensive_landed = 158.0

    s_cheap = calculate_cost_score(cheapest_landed, cheapest_landed)
    s_mid = calculate_cost_score(cheapest_landed, middle_landed)
    s_exp = calculate_cost_score(cheapest_landed, expensive_landed)

    assert s_cheap == 100.0
    assert s_cheap > s_mid > s_exp
    assert s_exp > 0.0
