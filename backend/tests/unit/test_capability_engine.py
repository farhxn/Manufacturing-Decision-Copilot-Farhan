"""
Tests for the Capability Engine.

Formula:
    match_score       = (matched_required / total_required) * 100   (100 if no requirements)
    capacity_component = clamp(production_capacity_pct, 0, 100)
    support_bonus     = 10.0 if engineering_support else 0.0
    score = match_score*0.70 + capacity_component*0.30 + support_bonus
    clamped to [0, 100]
"""
import pytest
from app.engines.capability import calculate_capability_score


# ── Perfect / worst ──────────────────────────────────────────────────────────

def test_capability_all_required_met_with_support():
    # Full capability match, full capacity, engineering support
    # score = 100*0.70 + 100*0.30 + 10 = 70+30+10 = 110 → clamped to 100
    score = calculate_capability_score(
        supplier_capabilities=["CNC Machining", "Assembly"],
        required_capabilities=["CNC Machining", "Assembly"],
        production_capacity_pct=100.0,
        engineering_support=True,
    )
    assert score == 100.0


def test_capability_no_capabilities_no_capacity_no_support():
    # Nothing matched, no capacity, no support → 0*0.70 + 0*0.30 + 0 = 0
    score = calculate_capability_score(
        supplier_capabilities=[],
        required_capabilities=["CNC Machining"],
        production_capacity_pct=0.0,
        engineering_support=False,
    )
    assert score == 0.0


# ── Requirement matching ─────────────────────────────────────────────────────

def test_capability_partial_match():
    # 1 of 2 required capabilities matched
    # match_score = 50; score = 50*0.70 + 100*0.30 = 35+30 = 65.0
    score = calculate_capability_score(
        supplier_capabilities=["CNC Machining"],
        required_capabilities=["CNC Machining", "Welding"],
        production_capacity_pct=100.0,
        engineering_support=False,
    )
    assert score == 65.0


def test_capability_no_match_zero_match_score():
    # Supplier has capabilities but none are required ones
    # match_score = 0; score = 0*0.70 + 100*0.30 = 30.0
    score = calculate_capability_score(
        supplier_capabilities=["Injection Molding"],
        required_capabilities=["CNC Machining", "Assembly"],
        production_capacity_pct=100.0,
        engineering_support=False,
    )
    assert score == 30.0


def test_capability_no_requirements_gives_full_match_score():
    # No required capabilities → match_score defaults to 100
    # score = 100*0.70 + 100*0.30 = 100.0
    score = calculate_capability_score(
        supplier_capabilities=["CNC Machining"],
        required_capabilities=[],
        production_capacity_pct=100.0,
        engineering_support=False,
    )
    assert score == 100.0


def test_capability_case_insensitive_matching():
    # Requirements and supplier capabilities compared case-insensitively
    score = calculate_capability_score(
        supplier_capabilities=["cnc machining", "ASSEMBLY"],
        required_capabilities=["CNC Machining", "Assembly"],
        production_capacity_pct=100.0,
        engineering_support=False,
    )
    assert score == 100.0


def test_capability_empty_supplier_capabilities_with_requirements():
    # Supplier offers nothing, requirements exist → match_score = 0
    # score = 0*0.70 + 80*0.30 = 24.0
    score = calculate_capability_score(
        supplier_capabilities=[],
        required_capabilities=["CNC Machining"],
        production_capacity_pct=80.0,
        engineering_support=False,
    )
    assert score == 24.0


# ── Engineering support bonus ────────────────────────────────────────────────

def test_capability_engineering_support_adds_bonus():
    # Same inputs, only engineering_support differs
    without = calculate_capability_score(
        supplier_capabilities=["CNC Machining"],
        required_capabilities=["CNC Machining"],
        production_capacity_pct=80.0,
        engineering_support=False,
    )
    with_support = calculate_capability_score(
        supplier_capabilities=["CNC Machining"],
        required_capabilities=["CNC Machining"],
        production_capacity_pct=80.0,
        engineering_support=True,
    )
    assert with_support == min(100.0, without + 10.0)


def test_capability_support_bonus_capped_at_100():
    # Full match + full capacity + support → 70+30+10=110 → capped at 100
    score = calculate_capability_score(
        supplier_capabilities=["CNC Machining"],
        required_capabilities=["CNC Machining"],
        production_capacity_pct=100.0,
        engineering_support=True,
    )
    assert score == 100.0


# ── Capacity component ───────────────────────────────────────────────────────

def test_capability_reduced_capacity_reduces_score():
    # match=100, capacity=50, no support: 100*0.70 + 50*0.30 = 70+15 = 85
    score = calculate_capability_score(
        supplier_capabilities=["CNC Machining"],
        required_capabilities=["CNC Machining"],
        production_capacity_pct=50.0,
        engineering_support=False,
    )
    assert score == 85.0


def test_capability_capacity_clamped_above_100():
    # capacity=120 → clamped to 100, same as capacity=100
    score_over = calculate_capability_score(
        supplier_capabilities=["CNC Machining"],
        required_capabilities=["CNC Machining"],
        production_capacity_pct=120.0,
        engineering_support=False,
    )
    score_normal = calculate_capability_score(
        supplier_capabilities=["CNC Machining"],
        required_capabilities=["CNC Machining"],
        production_capacity_pct=100.0,
        engineering_support=False,
    )
    assert score_over == score_normal


def test_capability_capacity_clamped_below_zero():
    # capacity=-10 → clamped to 0; score = 100*0.70 + 0*0.30 = 70.0
    score = calculate_capability_score(
        supplier_capabilities=["CNC Machining"],
        required_capabilities=["CNC Machining"],
        production_capacity_pct=-10.0,
        engineering_support=False,
    )
    assert score == 70.0


# ── Determinism ──────────────────────────────────────────────────────────────

def test_capability_is_deterministic():
    kwargs = dict(
        supplier_capabilities=["CNC Machining", "Assembly"],
        required_capabilities=["CNC Machining"],
        production_capacity_pct=90.0,
        engineering_support=True,
    )
    assert calculate_capability_score(**kwargs) == calculate_capability_score(**kwargs)
