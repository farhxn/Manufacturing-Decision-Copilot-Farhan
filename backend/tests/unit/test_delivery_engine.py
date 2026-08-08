"""
Tests for the Delivery Engine.

Formula:
    lead_time_component  = (min_lead_time / lead_time) * 100    weight 0.45
                           (0.0 if either lead time <= 0)
    on_time_component    = clamp(on_time_delivery_pct, 0, 100)  weight 0.35
    capacity_component   = clamp(production_capacity_pct, 0, 100) weight 0.20
    score = sum of weighted components, clamped to [0, 100]
"""
import pytest
from app.engines.delivery import calculate_delivery_score


# ── Perfect / worst ──────────────────────────────────────────────────────────

def test_delivery_fastest_supplier_gets_100():
    # When supplier lead time equals minimum, lead component = 100
    score = calculate_delivery_score(
        lead_time_days=10,
        min_lead_time_days=10,
        on_time_delivery_pct=100.0,
        production_capacity_pct=100.0,
    )
    assert score == 100.0


def test_delivery_slowest_meaningful_score():
    # lead_time=30, min=10 → lead_component=(10/30)*100=33.33
    # score = 33.33*0.45 + 100*0.35 + 100*0.20 = 15.0+35+20 = 70.0
    score = calculate_delivery_score(
        lead_time_days=30,
        min_lead_time_days=10,
        on_time_delivery_pct=100.0,
        production_capacity_pct=100.0,
    )
    assert score == round((10 / 30) * 100 * 0.45 + 100 * 0.35 + 100 * 0.20, 2)


# ── Zero / invalid lead time guards ─────────────────────────────────────────

def test_delivery_zero_lead_time_days_guard():
    # lead_time_days=0 → invalid, lead_component forced to 0
    # score = 0*0.45 + 100*0.35 + 100*0.20 = 55.0
    score = calculate_delivery_score(
        lead_time_days=0,
        min_lead_time_days=10,
        on_time_delivery_pct=100.0,
        production_capacity_pct=100.0,
    )
    assert score == 55.0


def test_delivery_zero_min_lead_time_guard():
    # min_lead_time_days=0 → invalid, lead_component forced to 0
    score = calculate_delivery_score(
        lead_time_days=14,
        min_lead_time_days=0,
        on_time_delivery_pct=100.0,
        production_capacity_pct=100.0,
    )
    assert score == 55.0


def test_delivery_negative_lead_time_treated_as_invalid():
    # Negative lead time → guard triggers, lead_component = 0
    score = calculate_delivery_score(
        lead_time_days=-5,
        min_lead_time_days=10,
        on_time_delivery_pct=100.0,
        production_capacity_pct=100.0,
    )
    assert score == 55.0


# ── Component weight isolation ───────────────────────────────────────────────

def test_delivery_only_lead_time_varies():
    # on_time=100, capacity=100 (perfect) — only lead time differs
    # lead_time=20, min=10 → lead_component=50
    # score = 50*0.45 + 100*0.35 + 100*0.20 = 22.5+35+20 = 77.5
    score = calculate_delivery_score(
        lead_time_days=20,
        min_lead_time_days=10,
        on_time_delivery_pct=100.0,
        production_capacity_pct=100.0,
    )
    assert score == 77.5


def test_delivery_only_on_time_varies():
    # lead_time==min (100), capacity=100 — only on_time changes
    # on_time=80 → score = 100*0.45 + 80*0.35 + 100*0.20 = 45+28+20 = 93.0
    score = calculate_delivery_score(
        lead_time_days=10,
        min_lead_time_days=10,
        on_time_delivery_pct=80.0,
        production_capacity_pct=100.0,
    )
    assert score == 93.0


def test_delivery_only_capacity_varies():
    # lead_time==min (100), on_time=100 — only capacity changes
    # capacity=50 → score = 100*0.45 + 100*0.35 + 50*0.20 = 45+35+10 = 90.0
    score = calculate_delivery_score(
        lead_time_days=10,
        min_lead_time_days=10,
        on_time_delivery_pct=100.0,
        production_capacity_pct=50.0,
    )
    assert score == 90.0


# ── Out-of-range input clamping ──────────────────────────────────────────────

def test_delivery_on_time_clamped_above_100():
    # on_time=110 → clamped to 100, result same as perfect
    score = calculate_delivery_score(
        lead_time_days=10,
        min_lead_time_days=10,
        on_time_delivery_pct=110.0,
        production_capacity_pct=100.0,
    )
    assert score == 100.0


def test_delivery_on_time_clamped_below_zero():
    # on_time=-10 → clamped to 0
    # score = 100*0.45 + 0*0.35 + 100*0.20 = 45+0+20 = 65.0
    score = calculate_delivery_score(
        lead_time_days=10,
        min_lead_time_days=10,
        on_time_delivery_pct=-10.0,
        production_capacity_pct=100.0,
    )
    assert score == 65.0


def test_delivery_capacity_clamped_below_zero():
    # capacity=-20 → clamped to 0
    # score = 100*0.45 + 100*0.35 + 0*0.20 = 45+35+0 = 80.0
    score = calculate_delivery_score(
        lead_time_days=10,
        min_lead_time_days=10,
        on_time_delivery_pct=100.0,
        production_capacity_pct=-20.0,
    )
    assert score == 80.0


# ── Realistic supplier profiles ──────────────────────────────────────────────

def test_delivery_realistic_fast_nearshore_supplier():
    # lead=10 days, min=10, on_time=97%, capacity=92%
    # lead_component=100, score = 100*0.45 + 97*0.35 + 92*0.20 = 45+33.95+18.4 = 97.35
    score = calculate_delivery_score(
        lead_time_days=10,
        min_lead_time_days=10,
        on_time_delivery_pct=97.0,
        production_capacity_pct=92.0,
    )
    assert score == 97.35


def test_delivery_realistic_slow_overseas_supplier():
    # lead=28, min=10, on_time=88%, capacity=85%
    # lead_component=(10/28)*100=35.71
    # score = 35.71*0.45 + 88*0.35 + 85*0.20 = 16.07+30.8+17 = 63.87 (approx)
    score = calculate_delivery_score(
        lead_time_days=28,
        min_lead_time_days=10,
        on_time_delivery_pct=88.0,
        production_capacity_pct=85.0,
    )
    expected = round((10 / 28) * 100 * 0.45 + 88.0 * 0.35 + 85.0 * 0.20, 2)
    assert score == expected


def test_delivery_default_capacity_is_100():
    # production_capacity_pct has a default of 100
    score_explicit = calculate_delivery_score(
        lead_time_days=10,
        min_lead_time_days=10,
        on_time_delivery_pct=100.0,
        production_capacity_pct=100.0,
    )
    score_default = calculate_delivery_score(
        lead_time_days=10,
        min_lead_time_days=10,
        on_time_delivery_pct=100.0,
    )
    assert score_explicit == score_default


def test_delivery_is_deterministic():
    kwargs = dict(
        lead_time_days=14,
        min_lead_time_days=10,
        on_time_delivery_pct=95.0,
        production_capacity_pct=88.0,
    )
    assert calculate_delivery_score(**kwargs) == calculate_delivery_score(**kwargs)
