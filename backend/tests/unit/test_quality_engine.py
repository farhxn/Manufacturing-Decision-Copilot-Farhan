"""
Tests for the Quality Engine.

Formula:
    defect_component    = 100 - clamp(defect_rate, 0, 100)          weight 0.40
    inspection_component = clamp(inspection_pass_rate, 0, 100)       weight 0.35
    rating_component    = clamp(((rating - 1) / 4) * 100, 0, 100)   weight 0.25
    score = sum of weighted components, clamped to [0, 100]
"""
import pytest
from app.engines.quality import calculate_quality_score


# ── Perfect / worst ──────────────────────────────────────────────────────────

def test_quality_perfect_supplier():
    # 0% defects, 100% inspection, 5-star → 100
    score = calculate_quality_score(
        defect_rate=0.0,
        inspection_pass_rate=100.0,
        customer_rating=5.0,
    )
    assert score == 100.0


def test_quality_worst_supplier():
    # 100% defects, 0% inspection, 1-star → 0
    score = calculate_quality_score(
        defect_rate=100.0,
        inspection_pass_rate=0.0,
        customer_rating=1.0,
    )
    assert score == 0.0


# ── Component weight isolation ───────────────────────────────────────────────

def test_quality_only_defect_rate_varies():
    # inspection=100, rating=5 (both perfect) — only defect_rate changes score
    # defect=50 → defect_component=50
    # score = 50*0.40 + 100*0.35 + 100*0.25 = 20 + 35 + 25 = 80
    score = calculate_quality_score(
        defect_rate=50.0,
        inspection_pass_rate=100.0,
        customer_rating=5.0,
    )
    assert score == 80.0


def test_quality_only_inspection_varies():
    # defect=0, rating=5 (both perfect) — only inspection changes score
    # inspection=50 → score = 100*0.40 + 50*0.35 + 100*0.25 = 40+17.5+25 = 82.5
    score = calculate_quality_score(
        defect_rate=0.0,
        inspection_pass_rate=50.0,
        customer_rating=5.0,
    )
    assert score == 82.5


def test_quality_only_rating_varies():
    # defect=0, inspection=100 (both perfect) — only rating changes score
    # rating=3.0 → rating_component = ((3-1)/4)*100 = 50
    # score = 100*0.40 + 100*0.35 + 50*0.25 = 40+35+12.5 = 87.5
    score = calculate_quality_score(
        defect_rate=0.0,
        inspection_pass_rate=100.0,
        customer_rating=3.0,
    )
    assert score == 87.5


# ── Rating scale normalization ───────────────────────────────────────────────

def test_quality_rating_minimum_boundary():
    # rating=1.0 → rating_component=0 → no contribution from rating
    # score = 100*0.40 + 100*0.35 + 0*0.25 = 75.0
    score = calculate_quality_score(
        defect_rate=0.0,
        inspection_pass_rate=100.0,
        customer_rating=1.0,
    )
    assert score == 75.0


def test_quality_rating_midpoint():
    # rating=3.0 → rating_component=50 (midpoint of 1–5 scale)
    score = calculate_quality_score(
        defect_rate=0.0,
        inspection_pass_rate=100.0,
        customer_rating=3.0,
    )
    assert score == 87.5


# ── Out-of-range input clamping ──────────────────────────────────────────────

def test_quality_defect_rate_clamped_above_100():
    # defect_rate=150 → clamped to 100 → defect_component=0
    # score = 0*0.40 + 100*0.35 + 100*0.25 = 60.0
    score = calculate_quality_score(
        defect_rate=150.0,
        inspection_pass_rate=100.0,
        customer_rating=5.0,
    )
    assert score == 60.0


def test_quality_defect_rate_clamped_below_zero():
    # defect_rate=-10 → clamped to 0 → defect_component=100 (treated as perfect)
    score = calculate_quality_score(
        defect_rate=-10.0,
        inspection_pass_rate=100.0,
        customer_rating=5.0,
    )
    assert score == 100.0


def test_quality_inspection_clamped_above_100():
    # inspection_pass_rate=120 → clamped to 100
    score = calculate_quality_score(
        defect_rate=0.0,
        inspection_pass_rate=120.0,
        customer_rating=5.0,
    )
    assert score == 100.0


def test_quality_rating_clamped_above_5():
    # customer_rating=6.0 → rating_component clamped to 100 → same as rating=5
    score = calculate_quality_score(
        defect_rate=0.0,
        inspection_pass_rate=100.0,
        customer_rating=6.0,
    )
    assert score == 100.0


def test_quality_rating_clamped_below_1():
    # customer_rating=0.0 → ((0-1)/4)*100 = -25 → clamped to 0
    # score = 100*0.40 + 100*0.35 + 0*0.25 = 75.0
    score = calculate_quality_score(
        defect_rate=0.0,
        inspection_pass_rate=100.0,
        customer_rating=0.0,
    )
    assert score == 75.0


# ── Realistic supplier profiles ──────────────────────────────────────────────

def test_quality_realistic_mixed_profile():
    # defect=4, inspection=94, rating=4.1
    # defect_component = 96; inspection_component = 94
    # rating_component = ((4.1-1)/4)*100 = (3.1/4)*100 = 77.5
    # score = 96*0.40 + 94*0.35 + 77.5*0.25 = 38.4+32.9+19.375 = 90.675 → 90.68
    score = calculate_quality_score(
        defect_rate=4.0,
        inspection_pass_rate=94.0,
        customer_rating=4.1,
    )
    assert score == 90.68


def test_quality_is_deterministic():
    kwargs = dict(defect_rate=2.5, inspection_pass_rate=97.0, customer_rating=4.5)
    assert calculate_quality_score(**kwargs) == calculate_quality_score(**kwargs)
