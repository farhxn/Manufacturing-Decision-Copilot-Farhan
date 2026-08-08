import pytest
from app.engines.risk import calculate_risk_score


def test_risk_score_all_zero():
    # No risk on any dimension → maximum safety score of 100
    score = calculate_risk_score(
        financial_risk=0.0,
        country_risk=0.0,
        supply_risk=0.0,
        compliance_risk=0.0,
        capacity_risk=0.0,
    )
    assert score == 100.0


def test_risk_score_all_hundred():
    # Maximum risk on every dimension → score clamped to 0
    score = calculate_risk_score(
        financial_risk=100.0,
        country_risk=100.0,
        supply_risk=100.0,
        compliance_risk=100.0,
        capacity_risk=100.0,
    )
    assert score == 0.0


def test_risk_score_mixed_values():
    # financial: 20*0.25=5, country: 30*0.20=6, supply: 40*0.20=8,
    # compliance: 10*0.20=2, capacity: 50*0.15=7.5 → total=28.5 → score=71.5
    score = calculate_risk_score(
        financial_risk=20.0,
        country_risk=30.0,
        supply_risk=40.0,
        compliance_risk=10.0,
        capacity_risk=50.0,
    )
    assert score == 71.5


def test_risk_score_upper_clamping():
    # Total risk exceeds 100 → score clamped to 0 (never negative)
    score = calculate_risk_score(
        financial_risk=200.0,
        country_risk=200.0,
        supply_risk=200.0,
        compliance_risk=200.0,
        capacity_risk=200.0,
    )
    assert score == 0.0


def test_risk_score_lower_clamping():
    # Negative risk magnitudes → score clamped to 100 (never above 100)
    score = calculate_risk_score(
        financial_risk=-50.0,
        country_risk=-50.0,
        supply_risk=-50.0,
        compliance_risk=-50.0,
        capacity_risk=-50.0,
    )
    assert score == 100.0


def test_risk_score_financial_risk_weight():
    # Only financial_risk set: 100*0.25=25 → score=75
    score = calculate_risk_score(
        financial_risk=100.0,
        country_risk=0.0,
        supply_risk=0.0,
        compliance_risk=0.0,
        capacity_risk=0.0,
    )
    assert score == 75.0


def test_risk_score_country_risk_weight():
    # Only country_risk set: 100*0.20=20 → score=80
    score = calculate_risk_score(
        financial_risk=0.0,
        country_risk=100.0,
        supply_risk=0.0,
        compliance_risk=0.0,
        capacity_risk=0.0,
    )
    assert score == 80.0


def test_risk_score_supply_risk_weight():
    # Only supply_risk set: 100*0.20=20 → score=80
    score = calculate_risk_score(
        financial_risk=0.0,
        country_risk=0.0,
        supply_risk=100.0,
        compliance_risk=0.0,
        capacity_risk=0.0,
    )
    assert score == 80.0


def test_risk_score_compliance_risk_weight():
    # Only compliance_risk set: 100*0.20=20 → score=80
    score = calculate_risk_score(
        financial_risk=0.0,
        country_risk=0.0,
        supply_risk=0.0,
        compliance_risk=100.0,
        capacity_risk=0.0,
    )
    assert score == 80.0


def test_risk_score_capacity_risk_weight():
    # Only capacity_risk set: 100*0.15=15 → score=85
    score = calculate_risk_score(
        financial_risk=0.0,
        country_risk=0.0,
        supply_risk=0.0,
        compliance_risk=0.0,
        capacity_risk=100.0,
    )
    assert score == 85.0


def test_risk_score_weights_sum_to_one():
    # Setting all inputs to the same value X should give score = 100 - X
    # because weights sum to 1.0: 0.25+0.20+0.20+0.20+0.15 = 1.0
    for x in [10.0, 50.0, 75.0]:
        score = calculate_risk_score(
            financial_risk=x,
            country_risk=x,
            supply_risk=x,
            compliance_risk=x,
            capacity_risk=x,
        )
        assert score == round(100.0 - x, 2), f"failed for x={x}"


def test_risk_score_low_risk_supplier():
    # Realistic low-risk German supplier profile
    # financial=5*0.25=1.25, country=8*0.20=1.6, supply=6*0.20=1.2,
    # compliance=4*0.20=0.8, capacity=5*0.15=0.75 → total=5.6 → score=94.4
    score = calculate_risk_score(
        financial_risk=5.0,
        country_risk=8.0,
        supply_risk=6.0,
        compliance_risk=4.0,
        capacity_risk=5.0,
    )
    assert score == 94.4


def test_risk_score_high_risk_supplier():
    # Realistic high-risk emerging-market supplier profile
    # financial=30*0.25=7.5, country=35*0.20=7.0, supply=32*0.20=6.4,
    # compliance=25*0.20=5.0, capacity=28*0.15=4.2 → total=30.1 → score=69.9
    score = calculate_risk_score(
        financial_risk=30.0,
        country_risk=35.0,
        supply_risk=32.0,
        compliance_risk=25.0,
        capacity_risk=28.0,
    )
    assert score == 69.9


def test_risk_score_is_deterministic():
    # Same inputs always produce the same output
    kwargs = dict(
        financial_risk=15.0,
        country_risk=20.0,
        supply_risk=18.0,
        compliance_risk=12.0,
        capacity_risk=22.0,
    )
    assert calculate_risk_score(**kwargs) == calculate_risk_score(**kwargs)
