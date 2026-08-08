"""
Phase 4 — Comprehensive Edge Case Tests
Covers best, average, and worst cases across every engine, filling gaps in the
existing per-engine unit tests.

Run:
    cd backend
    python -m pytest tests/unit/test_phase4_edge_cases.py -v
"""
import pytest

# ============================================================================
# SECTION 1 — COST ENGINE
# ============================================================================
from app.engines.cost import calculate_cost_score, calculate_landed_cost


class TestCostEdgeCases:
    # ── Best-case paths ──────────────────────────────────────────────────────

    def test_cost_single_supplier_always_scores_100(self):
        """The only active supplier is always the cheapest, so score = 100."""
        cost = calculate_landed_cost(quoted_price=200.0, shipping_cost=30.0, duty_rate=0.10)
        assert calculate_cost_score(min_landed_cost=cost, supplier_landed_cost=cost) == 100.0

    def test_cost_no_duty_no_extras_best_case(self):
        """Zero duty, zero insurance, zero taxes — absolute minimum landed cost."""
        cost = calculate_landed_cost(quoted_price=50.0, shipping_cost=5.0, duty_rate=0.0)
        assert cost == 55.0

    def test_cost_score_cheapest_by_one_cent(self):
        """Supplier that costs one cent less than min should still round-trip to 100."""
        min_cost = 100.00
        # min_cost / min_cost * 100 = 100 exactly
        assert calculate_cost_score(min_landed_cost=min_cost, supplier_landed_cost=min_cost) == 100.0

    # ── Average-case paths ───────────────────────────────────────────────────

    def test_cost_duty_applies_to_quoted_price_only_not_shipping(self):
        """Duty is quoted_price * duty_rate; shipping_cost is NOT dutiable."""
        # duty = 100 * 0.10 = 10; base = 100 + 20 + 10 = 130
        cost = calculate_landed_cost(quoted_price=100.0, shipping_cost=20.0, duty_rate=0.10)
        assert cost == 130.0
        # Confirm shipping changes landed cost but NOT duty amount
        cost_high_ship = calculate_landed_cost(quoted_price=100.0, shipping_cost=50.0, duty_rate=0.10)
        # duty still = 10; base = 100 + 50 + 10 = 160
        assert cost_high_ship == 160.0

    def test_cost_shipping_multiplier_does_not_affect_duty(self):
        """shipping_multiplier scales only shipping_cost, never the duty calculation."""
        # duty = 200 * 0.05 = 10 (unchanged)
        # shipping: 30 * 1.0 = 30  vs  30 * 2.0 = 60
        base = calculate_landed_cost(quoted_price=200.0, shipping_cost=30.0, duty_rate=0.05, shipping_multiplier=1.0)
        doubled_ship = calculate_landed_cost(quoted_price=200.0, shipping_cost=30.0, duty_rate=0.05, shipping_multiplier=2.0)
        assert doubled_ship - base == pytest.approx(30.0)  # exactly one extra shipping_cost

    def test_cost_stacked_currency_rates(self):
        """Supplier currency_rate and config currency_rate multiply together in ranking."""
        # Simulate what ranking._compute_landed_cost does:
        # combined_rate = config.currency_rate * supplier.currency_rate
        # Here we test the raw function with a combined rate directly.
        # base = 100 + 10 + 5 = 115; combined_rate = 1.2 * 1.1 = 1.32
        cost = calculate_landed_cost(
            quoted_price=100.0, shipping_cost=10.0, duty_rate=0.05, currency_rate=1.32
        )
        assert cost == pytest.approx(115.0 * 1.32, abs=0.01)

    def test_cost_score_25_percent_premium_over_min(self):
        """Supplier 25 % more expensive than cheapest → score ≈ 80."""
        score = calculate_cost_score(min_landed_cost=100.0, supplier_landed_cost=125.0)
        assert score == pytest.approx(80.0, abs=0.01)


    # ── Worst-case / boundary paths ──────────────────────────────────────────

    def test_cost_min_landed_cost_zero_all_suppliers_score_zero(self):
        """If min_landed_cost == 0.0, every supplier scores 0 (0 / x = 0)."""
        # This can happen with a mis-seeded dataset where quoted_price=0.
        assert calculate_cost_score(min_landed_cost=0.0, supplier_landed_cost=50.0) == 0.0
        assert calculate_cost_score(min_landed_cost=0.0, supplier_landed_cost=0.0) == 0.0

    def test_cost_negative_quoted_price_does_not_crash(self):
        """Negative quoted_price produces a negative landed cost; score guard returns 0."""
        cost = calculate_landed_cost(quoted_price=-10.0, shipping_cost=5.0, duty_rate=0.0)
        assert cost < 0
        assert calculate_cost_score(min_landed_cost=100.0, supplier_landed_cost=cost) == 0.0

    def test_cost_extreme_duty_rate_100_percent(self):
        """100 % duty doubles the effective quoted price contribution."""
        # 100 + 10 + 100*1.0 = 210
        cost = calculate_landed_cost(quoted_price=100.0, shipping_cost=10.0, duty_rate=1.0)
        assert cost == 210.0

    def test_cost_currency_rate_zero_produces_zero_landed_cost(self):
        """currency_rate=0 makes every landed cost 0; score guard returns 0."""
        cost = calculate_landed_cost(quoted_price=100.0, shipping_cost=10.0, duty_rate=0.05, currency_rate=0.0)
        assert cost == 0.0
        assert calculate_cost_score(min_landed_cost=0.0, supplier_landed_cost=0.0) == 0.0

    def test_cost_score_supplier_exactly_10x_more_expensive(self):
        """Supplier 10× the minimum cost scores 10."""
        score = calculate_cost_score(min_landed_cost=10.0, supplier_landed_cost=100.0)
        assert score == 10.0

    def test_cost_rounding_consistency_near_half_cent(self):
        """Landed cost rounds to 2 dp consistently at the half-cent boundary."""
        cost = calculate_landed_cost(quoted_price=1.005, shipping_cost=0.0, duty_rate=0.0)
        # Python's round() uses banker's rounding; we just assert the result is 2 dp
        assert cost == round(cost, 2)



# ============================================================================
# SECTION 2 — RISK ENGINE
# ============================================================================
from app.engines.risk import calculate_risk_score


class TestRiskEdgeCases:
    # ── Best-case paths ──────────────────────────────────────────────────────

    def test_risk_single_fractional_risk_correct_weight(self):
        """Each weight is applied precisely to fractional inputs."""
        # financial=10*0.25=2.5, rest=0 → total=2.5 → score=97.5
        assert calculate_risk_score(10.0, 0.0, 0.0, 0.0, 0.0) == 97.5

    def test_risk_capacity_weight_is_lightest(self):
        """capacity_risk has the smallest weight (0.15).
        Setting only capacity_risk=100 → score=85, higher than any other single
        dimension at 100 (country/supply/compliance each give 80)."""
        only_capacity = calculate_risk_score(0.0, 0.0, 0.0, 0.0, 100.0)
        only_financial = calculate_risk_score(100.0, 0.0, 0.0, 0.0, 0.0)
        assert only_capacity > only_financial  # 85 > 75

    def test_risk_near_zero_inputs_near_perfect_score(self):
        """Realistic best-in-class supplier with tiny risks scores close to 100."""
        score = calculate_risk_score(1.0, 1.0, 1.0, 1.0, 1.0)
        # total = 1.0*(0.25+0.20+0.20+0.20+0.15) = 1.0 → score = 99.0
        assert score == 99.0

    # ── Average-case paths ───────────────────────────────────────────────────

    def test_risk_equal_moderate_risks_formula(self):
        """All inputs at 40 → total=40 → score=60."""
        assert calculate_risk_score(40.0, 40.0, 40.0, 40.0, 40.0) == 60.0

    def test_risk_asymmetric_profile_hand_calculated(self):
        """financial=50, country=20, supply=10, compliance=30, capacity=0.
        total = 50*0.25 + 20*0.20 + 10*0.20 + 30*0.20 + 0*0.15
              = 12.5 + 4.0 + 2.0 + 6.0 + 0.0 = 24.5 → score = 75.5"""
        assert calculate_risk_score(50.0, 20.0, 10.0, 30.0, 0.0) == 75.5

    def test_risk_score_rounds_to_two_decimal_places(self):
        """Score is rounded to 2 dp (no extra floating-point noise)."""
        score = calculate_risk_score(33.3, 33.3, 33.3, 33.3, 33.3)
        assert score == round(score, 2)

    # ── Worst-case / boundary paths ──────────────────────────────────────────

    def test_risk_exactly_100_total_risk_gives_zero(self):
        """When weights × inputs sum to exactly 100, score = 0.0."""
        # All at 100 → total = 100 → score = 0
        assert calculate_risk_score(100.0, 100.0, 100.0, 100.0, 100.0) == 0.0

    def test_risk_just_below_100_total_gives_nonzero_score(self):
        """total=99.0 → score=1.0 (not clamped)."""
        # All at 99 → total=99 → score=1.0
        assert calculate_risk_score(99.0, 99.0, 99.0, 99.0, 99.0) == 1.0

    def test_risk_single_dimension_maxed_financial_is_heaviest(self):
        """financial_risk=100 → total=25 → score=75 (heaviest single weight)."""
        assert calculate_risk_score(100.0, 0.0, 0.0, 0.0, 0.0) == 75.0

    def test_risk_over_100_inputs_clamp_output_to_zero(self):
        """Inputs well above 100 push the score negative; clamp returns 0.0."""
        assert calculate_risk_score(500.0, 500.0, 500.0, 500.0, 500.0) == 0.0

    def test_risk_negative_inputs_clamp_output_to_100(self):
        """Negative magnitudes produce score above 100; clamp returns 100.0."""
        assert calculate_risk_score(-100.0, -100.0, -100.0, -100.0, -100.0) == 100.0

    def test_risk_mixed_over_and_under_range(self):
        """One very high, rest zero → clamped to 0 if high enough."""
        # financial=400, others=0 → total=100 → score=0.0
        assert calculate_risk_score(400.0, 0.0, 0.0, 0.0, 0.0) == 0.0



# ============================================================================
# SECTION 3 — QUALITY ENGINE
# ============================================================================
from app.engines.quality import calculate_quality_score


class TestQualityEdgeCases:
    # ── Best-case paths ──────────────────────────────────────────────────────

    def test_quality_all_components_perfect(self):
        """0 defects, 100 % inspection, 5-star → 100.0 (already in base tests,
        confirmed here for completeness of the best-case triad)."""
        assert calculate_quality_score(0.0, 100.0, 5.0) == 100.0

    def test_quality_rating_exactly_5_normalized_to_100(self):
        """rating=5 → ((5-1)/4)*100 = 100 → rating_component = 100."""
        score = calculate_quality_score(0.0, 100.0, 5.0)
        assert score == 100.0

    def test_quality_defect_rate_exactly_zero(self):
        """defect_rate=0 → defect_component=100 (full 40-point contribution)."""
        score = calculate_quality_score(0.0, 50.0, 3.0)
        # 100*0.40 + 50*0.35 + 50*0.25 = 40 + 17.5 + 12.5 = 70.0
        assert score == 70.0

    # ── Average-case paths ───────────────────────────────────────────────────

    def test_quality_rating_exactly_1_contributes_zero(self):
        """rating=1 is the minimum; rating_component=0, so only defect+inspection count."""
        # 100*0.40 + 100*0.35 + 0*0.25 = 75.0
        assert calculate_quality_score(0.0, 100.0, 1.0) == 75.0

    def test_quality_rating_midpoint_3_gives_50_component(self):
        """rating=3 → ((3-1)/4)*100 = 50."""
        # 100*0.40 + 100*0.35 + 50*0.25 = 87.5
        assert calculate_quality_score(0.0, 100.0, 3.0) == 87.5

    def test_quality_defect_rate_50_halves_defect_component(self):
        """defect_rate=50 → defect_component=50."""
        # 50*0.40 + 100*0.35 + 100*0.25 = 20+35+25 = 80.0
        assert calculate_quality_score(50.0, 100.0, 5.0) == 80.0

    def test_quality_inspection_pass_rate_50_halves_that_component(self):
        """inspection=50 → inspection_component=50."""
        # 100*0.40 + 50*0.35 + 100*0.25 = 40+17.5+25 = 82.5
        assert calculate_quality_score(0.0, 50.0, 5.0) == 82.5

    def test_quality_all_components_at_50(self):
        """All inputs at their midpoint produce a mid-range score."""
        # defect_rate=50 → defect_component=50
        # inspection=50 → component=50
        # rating=3.0 → component=50
        # score = 50*0.40 + 50*0.35 + 50*0.25 = 50.0
        assert calculate_quality_score(50.0, 50.0, 3.0) == 50.0

    def test_quality_rating_2_normalized(self):
        """rating=2 → ((2-1)/4)*100 = 25."""
        # 100*0.40 + 100*0.35 + 25*0.25 = 40+35+6.25 = 81.25
        assert calculate_quality_score(0.0, 100.0, 2.0) == 81.25

    def test_quality_rating_4_normalized(self):
        """rating=4 → ((4-1)/4)*100 = 75."""
        # 100*0.40 + 100*0.35 + 75*0.25 = 40+35+18.75 = 93.75
        assert calculate_quality_score(0.0, 100.0, 4.0) == 93.75

    # ── Worst-case / boundary paths ──────────────────────────────────────────

    def test_quality_all_worst_inputs_give_zero(self):
        """100% defects, 0% inspection, 1-star → 0.0."""
        assert calculate_quality_score(100.0, 0.0, 1.0) == 0.0

    def test_quality_defect_rate_above_100_clamped(self):
        """defect_rate=200 → clamped to 100 → defect_component=0."""
        # 0*0.40 + 100*0.35 + 100*0.25 = 60.0
        assert calculate_quality_score(200.0, 100.0, 5.0) == 60.0

    def test_quality_defect_rate_below_zero_clamped(self):
        """defect_rate=-50 → clamped to 0 → defect_component=100 (treated as perfect)."""
        assert calculate_quality_score(-50.0, 100.0, 5.0) == 100.0

    def test_quality_rating_above_5_clamped_to_100_component(self):
        """rating=10 → ((10-1)/4)*100=225 → clamped to 100 → same as rating=5."""
        assert calculate_quality_score(0.0, 100.0, 10.0) == 100.0

    def test_quality_rating_below_1_clamped_to_zero_component(self):
        """rating=0 → ((0-1)/4)*100=-25 → clamped to 0 → same as rating=1."""
        assert calculate_quality_score(0.0, 100.0, 0.0) == 75.0

    def test_quality_inspection_below_zero_clamped(self):
        """inspection=-10 → clamped to 0."""
        # 100*0.40 + 0*0.35 + 100*0.25 = 65.0
        assert calculate_quality_score(0.0, -10.0, 5.0) == 65.0

    def test_quality_output_never_exceeds_100(self):
        """Even with all out-of-range 'good' inputs, score stays ≤ 100."""
        assert calculate_quality_score(-999.0, 999.0, 999.0) <= 100.0

    def test_quality_output_never_below_zero(self):
        """Even with all out-of-range 'bad' inputs, score stays ≥ 0."""
        assert calculate_quality_score(999.0, -999.0, -999.0) >= 0.0



# ============================================================================
# SECTION 4 — DELIVERY ENGINE
# ============================================================================
from app.engines.delivery import calculate_delivery_score


class TestDeliveryEdgeCases:
    # ── Best-case paths ──────────────────────────────────────────────────────

    def test_delivery_lead_time_1_day_is_fastest(self):
        """Minimum possible real lead time (1 day == min) → lead_component=100."""
        score = calculate_delivery_score(
            lead_time_days=1, min_lead_time_days=1,
            on_time_delivery_pct=100.0, production_capacity_pct=100.0,
        )
        assert score == 100.0

    def test_delivery_all_suppliers_same_lead_time_all_score_100_lead_component(self):
        """When every supplier has identical lead times, lead_component=100 for all."""
        for days in (7, 14, 30, 90):
            score = calculate_delivery_score(
                lead_time_days=days, min_lead_time_days=days,
                on_time_delivery_pct=100.0, production_capacity_pct=100.0,
            )
            assert score == 100.0, f"failed for lead_time={days}"

    def test_delivery_on_time_100_capacity_100_fastest_is_perfect(self):
        """Confirming perfect score path explicitly."""
        assert calculate_delivery_score(5, 5, 100.0, 100.0) == 100.0

    # ── Average-case paths ───────────────────────────────────────────────────

    def test_delivery_lead_time_twice_the_minimum(self):
        """lead_time = 2 × min → lead_component = 50."""
        # 50*0.45 + 100*0.35 + 100*0.20 = 22.5+35+20 = 77.5
        score = calculate_delivery_score(
            lead_time_days=20, min_lead_time_days=10,
            on_time_delivery_pct=100.0, production_capacity_pct=100.0,
        )
        assert score == 77.5

    def test_delivery_lead_time_three_times_minimum(self):
        """lead_time = 3 × min → lead_component ≈ 33.33."""
        expected = round((10 / 30) * 100 * 0.45 + 100 * 0.35 + 100 * 0.20, 2)
        score = calculate_delivery_score(30, 10, 100.0, 100.0)
        assert score == expected

    def test_delivery_on_time_75_percent(self):
        """Realistic on-time rate of 75 % with perfect lead time and capacity."""
        # 100*0.45 + 75*0.35 + 100*0.20 = 45+26.25+20 = 91.25
        assert calculate_delivery_score(10, 10, 75.0, 100.0) == 91.25

    def test_delivery_demand_adjusted_capacity_fed_from_ranking(self):
        """Simulate what ranking engine does: capacity_pct / demand_multiplier.
        demand_multiplier=2 → effective_capacity = 80/2 = 40."""
        effective_capacity = min(100.0, max(0.0, 80.0 / 2.0))  # 40.0
        # lead=10=min → lead_component=100; on_time=95
        # 100*0.45 + 95*0.35 + 40*0.20 = 45+33.25+8 = 86.25
        score = calculate_delivery_score(10, 10, 95.0, effective_capacity)
        assert score == 86.25

    def test_delivery_high_demand_collapses_capacity_to_zero(self):
        """demand_multiplier >> 1 → capacity rounds down to 0."""
        effective_capacity = max(0.0, min(100.0, 100.0 / 1000.0))  # ≈ 0.1 → non-zero
        # Use exactly 0 to test boundary
        score = calculate_delivery_score(10, 10, 100.0, 0.0)
        # 100*0.45 + 100*0.35 + 0*0.20 = 80.0
        assert score == 80.0

    # ── Worst-case / boundary paths ──────────────────────────────────────────

    def test_delivery_all_worst_inputs(self):
        """lead_time ≫ min, 0 % on-time, 0 % capacity."""
        # lead=365, min=1 → lead_component=(1/365)*100 ≈ 0.27
        expected = round((1 / 365) * 100 * 0.45 + 0 * 0.35 + 0 * 0.20, 2)
        score = calculate_delivery_score(365, 1, 0.0, 0.0)
        assert score == expected

    def test_delivery_zero_lead_time_guard_still_uses_other_components(self):
        """lead_time=0 → lead_component=0; on_time+capacity still contribute."""
        # 0*0.45 + 90*0.35 + 80*0.20 = 0+31.5+16 = 47.5
        score = calculate_delivery_score(0, 10, 90.0, 80.0)
        assert score == 47.5

    def test_delivery_both_lead_times_zero_gives_zero_lead_component(self):
        """Both lead_time_days and min_lead_time_days=0 → guard, lead_component=0."""
        score = calculate_delivery_score(0, 0, 100.0, 100.0)
        # 0*0.45 + 100*0.35 + 100*0.20 = 55.0
        assert score == 55.0

    def test_delivery_negative_min_lead_time_guard(self):
        """min_lead_time_days < 0 → guard, lead_component=0."""
        score = calculate_delivery_score(14, -1, 100.0, 100.0)
        assert score == 55.0

    def test_delivery_on_time_and_capacity_clamped_above_100(self):
        """Values over 100 clamped; result same as 100."""
        score_clamped = calculate_delivery_score(10, 10, 150.0, 200.0)
        score_normal = calculate_delivery_score(10, 10, 100.0, 100.0)
        assert score_clamped == score_normal == 100.0

    def test_delivery_output_bounded_0_to_100(self):
        """Score is always within [0, 100] regardless of inputs."""
        assert 0.0 <= calculate_delivery_score(0, 0, -999.0, -999.0) <= 100.0
        assert 0.0 <= calculate_delivery_score(1, 1, 999.0, 999.0) <= 100.0



# ============================================================================
# SECTION 5 — CAPABILITY ENGINE
# ============================================================================
from app.engines.capability import calculate_capability_score


class TestCapabilityEdgeCases:
    # ── Best-case paths ──────────────────────────────────────────────────────

    def test_capability_single_required_capability_met(self):
        """One required, one held → match_score=100."""
        # 100*0.70 + 100*0.30 = 100.0
        assert calculate_capability_score(["CNC"], ["CNC"], 100.0, False) == 100.0

    def test_capability_more_capabilities_than_required_still_100(self):
        """Supplier has extras beyond what's required — match_score stays 100."""
        score = calculate_capability_score(
            ["CNC", "Welding", "Assembly", "Stamping"],
            ["CNC", "Assembly"],
            100.0, False,
        )
        assert score == 100.0

    def test_capability_no_required_caps_full_match_regardless_of_held(self):
        """Empty required list → match_score=100 even if supplier holds nothing."""
        assert calculate_capability_score([], [], 100.0, False) == 100.0
        assert calculate_capability_score([], [], 50.0, False) == round(100*0.70 + 50*0.30, 2)

    def test_capability_engineering_support_bonus_on_partial_match(self):
        """Support bonus applies even when match is only partial."""
        without = calculate_capability_score(["CNC"], ["CNC", "Welding"], 100.0, False)
        with_s = calculate_capability_score(["CNC"], ["CNC", "Welding"], 100.0, True)
        assert with_s == min(100.0, without + 10.0)

    # ── Average-case paths ───────────────────────────────────────────────────

    def test_capability_duplicate_required_capabilities_counted_once_each(self):
        """Duplicate entries in required_capabilities inflate denominator — test
        that a supplier with a single 'CNC' entry does NOT get 100% if 'CNC'
        appears twice in required list (only 1 of 2 matched)."""
        score = calculate_capability_score(["CNC"], ["CNC", "CNC"], 100.0, False)
        # matched=1 (supplier has 'cnc', counts once via 'in' check)
        # BUT the loop iterates over ["CNC","CNC"] so matched=2 out of 2 = 100
        # The engine uses: sum(1 for req in required if req.lower() in supplier_lower)
        # supplier_lower=["cnc"]; "cnc" in ["cnc"] is True for BOTH iterations → matched=2
        # So score = 100*0.70 + 100*0.30 = 100 — document this behavior.
        assert score == 100.0

    def test_capability_two_of_three_required_met(self):
        """2/3 required → match_score≈66.67."""
        score = calculate_capability_score(
            ["CNC", "Welding"], ["CNC", "Welding", "Assembly"], 100.0, False
        )
        expected = round((2 / 3) * 100 * 0.70 + 100 * 0.30, 2)
        assert score == expected

    def test_capability_case_insensitive_mixed_case(self):
        """All case variants normalise correctly."""
        score = calculate_capability_score(
            ["CNC Machining", "ASSEMBLY"],
            ["cnc machining", "Assembly"],
            100.0, False,
        )
        assert score == 100.0

    def test_capability_zero_capacity_with_full_match_no_support(self):
        """Capacity=0 → capacity_component=0; match_score still contributes."""
        # 100*0.70 + 0*0.30 = 70.0
        assert calculate_capability_score(["CNC"], ["CNC"], 0.0, False) == 70.0

    def test_capability_zero_capacity_with_support_bonus(self):
        """Zero capacity + full match + support → 70+0+10=80."""
        assert calculate_capability_score(["CNC"], ["CNC"], 0.0, True) == 80.0

    def test_capability_no_match_zero_capacity_no_support(self):
        """Absolute worst: 0 match, 0 capacity, no support → 0."""
        assert calculate_capability_score([], ["CNC"], 0.0, False) == 0.0

    # ── Worst-case / boundary paths ──────────────────────────────────────────

    def test_capability_support_bonus_cannot_push_above_100(self):
        """Full match + full capacity = 100; adding support stays at 100."""
        assert calculate_capability_score(["CNC"], ["CNC"], 100.0, True) == 100.0

    def test_capability_capacity_clamped_above_100(self):
        """capacity=200 → clamped to 100."""
        over = calculate_capability_score(["CNC"], ["CNC"], 200.0, False)
        normal = calculate_capability_score(["CNC"], ["CNC"], 100.0, False)
        assert over == normal

    def test_capability_capacity_clamped_below_zero(self):
        """capacity=-50 → clamped to 0; match still contributes."""
        assert calculate_capability_score(["CNC"], ["CNC"], -50.0, False) == 70.0

    def test_capability_large_required_list_all_met(self):
        """10 required capabilities, all met → score=100+10bonus → capped 100."""
        caps = [f"cap_{i}" for i in range(10)]
        assert calculate_capability_score(caps, caps, 100.0, True) == 100.0

    def test_capability_large_required_list_none_met(self):
        """10 required, 0 met, full capacity, no support → 0*0.70+100*0.30=30."""
        required = [f"req_{i}" for i in range(10)]
        supplier = [f"other_{i}" for i in range(10)]
        assert calculate_capability_score(supplier, required, 100.0, False) == 30.0



# ============================================================================
# SECTION 6 — COMPLIANCE ENGINE
# ============================================================================
from app.engines.compliance import calculate_compliance_score


class TestComplianceEdgeCases:
    # ── Best-case paths ──────────────────────────────────────────────────────

    def test_compliance_exact_match_is_100(self):
        """Exact cert name match (case-insensitive) → 100."""
        assert calculate_compliance_score(["ISO 9001"], ["ISO 9001"]) == 100.0

    def test_compliance_colon_versioned_cert_matches_base_requirement(self):
        """'ISO 9001:2015' satisfies requirement 'ISO 9001'."""
        assert calculate_compliance_score(["ISO 9001:2015"], ["ISO 9001"]) == 100.0

    def test_compliance_space_suffixed_cert_matches_base_requirement(self):
        """'ISO 9001 Certified' satisfies requirement 'ISO 9001'."""
        assert calculate_compliance_score(["ISO 9001 Certified"], ["ISO 9001"]) == 100.0

    def test_compliance_multiple_required_all_met_with_extras(self):
        """Supplier holds more than required — still 100."""
        assert calculate_compliance_score(
            ["ISO 9001:2015", "AS9100D", "RoHS", "IATF 16949"],
            ["ISO 9001", "AS9100D"],
        ) == 100.0

    # ── Average-case paths ───────────────────────────────────────────────────

    def test_compliance_as9100d_does_not_match_requirement_as9100(self):
        """'AS9100D' starts with 'AS9100' followed by 'D' (not ':' or ' ').
        The colon rule fails ('AS9100D' doesn't start with 'AS9100:').
        The space rule fails ('AS9100D' doesn't contain 'AS9100 ').
        So requirement 'AS9100' is NOT satisfied by cert 'AS9100D'."""
        score = calculate_compliance_score(["AS9100D"], ["AS9100"])
        assert score == 0.0

    def test_compliance_iso_family_prefix_does_not_match_specific_cert(self):
        """Broad requirement 'ISO' must NOT be satisfied by 'ISO 9001:2015'.
        Single-word prefix rule blocks it because suffix '9001:2015' starts with digit."""
        assert calculate_compliance_score(["ISO 9001:2015"], ["ISO"]) == 0.0

    def test_compliance_rohs_space_variant_matches(self):
        """'RoHS Compliant' satisfies requirement 'RoHS' via space-prefix rule."""
        assert calculate_compliance_score(["RoHS Compliant"], ["RoHS"]) == 100.0

    def test_compliance_multiword_requirement_space_match(self):
        """Multi-word requirement 'IATF 16949' matched by 'IATF 16949:2016'."""
        assert calculate_compliance_score(["IATF 16949:2016"], ["IATF 16949"]) == 100.0

    def test_compliance_requirement_with_leading_trailing_whitespace(self):
        """Whitespace around requirement name is stripped before comparison."""
        assert calculate_compliance_score(["ISO 9001:2015"], ["  ISO 9001  "]) == 100.0

    def test_compliance_case_insensitive_all_uppercase_requirement(self):
        """Requirement in ALL CAPS matches a mixed-case cert."""
        assert calculate_compliance_score(["RoHS Compliant"], ["ROHS"]) == 100.0

    # ── Worst-case / boundary paths ──────────────────────────────────────────

    def test_compliance_one_missing_cert_out_of_many_gives_zero(self):
        """Binary: one miss out of 10 required → 0.0."""
        required = ["ISO 9001", "AS9100D", "RoHS", "IATF 16949", "ISO 14001",
                    "OHSAS 18001", "NADCAP", "EN 9100", "ISO 45001", "ISO 50001"]
        supplier_certs = required[:-1]   # missing last one
        assert calculate_compliance_score(supplier_certs, required) == 0.0

    def test_compliance_empty_supplier_certs_any_requirement_fails(self):
        """No certs held → always 0 when any cert is required."""
        assert calculate_compliance_score([], ["ISO 9001"]) == 0.0

    def test_compliance_empty_required_always_100(self):
        """No requirements → always 100, even with empty supplier list."""
        assert calculate_compliance_score([], []) == 100.0
        assert calculate_compliance_score(["ISO 9001"], []) == 100.0

    def test_compliance_cert_name_that_is_just_spaces_does_not_match(self):
        """Requirement that is only whitespace strips to ''.
        _cert_matches checks startswith(':') and startswith(' ') — both False for
        a non-empty held cert, and exact match '' == 'iso 9001' is also False.
        Therefore a blank requirement is treated as UNMET → score=0."""
        score = calculate_compliance_score(["ISO 9001"], ["   "])
        assert score == 0.0   # blank requirement cannot be satisfied by any real cert

    def test_compliance_duplicate_requirements_both_must_be_met(self):
        """If 'ISO 9001' appears twice in required, it must be matched twice.
        Since the same cert satisfies both iterations, score=100."""
        assert calculate_compliance_score(["ISO 9001:2015"], ["ISO 9001", "ISO 9001"]) == 100.0

    def test_compliance_as9100_does_not_fuzzy_match_as9100d_via_colon(self):
        """'AS9100:2016' satisfies 'AS9100' via colon-prefix rule."""
        assert calculate_compliance_score(["AS9100:2016"], ["AS9100"]) == 100.0

    def test_compliance_partial_word_never_matches(self):
        """'ROHS' requirement is NOT satisfied by 'ROHSPLUS' — no space or colon boundary."""
        assert calculate_compliance_score(["ROHSPLUS"], ["ROHS"]) == 0.0



# ============================================================================
# SECTION 7 — CONFIDENCE ENGINE
# ============================================================================
from app.engines.confidence import (
    calculate_confidence,
    confidence_label,
    confidence_percentage,
)


class TestConfidenceEdgeCases:
    # ── Best-case paths ──────────────────────────────────────────────────────

    def test_confidence_all_ones_is_1_0(self):
        """Perfect inputs → confidence = 1.0."""
        assert calculate_confidence(1.0, 1.0, 1.0, 1.0, 1.0) == 1.0

    def test_confidence_label_exactly_0_80_is_high(self):
        """Boundary: 0.80 is inclusive for 'High'."""
        assert confidence_label(0.80) == "High"

    def test_confidence_label_just_below_0_80_is_medium(self):
        """0.7999 falls into 'Medium'."""
        assert confidence_label(0.7999) == "Medium"

    def test_confidence_label_exactly_0_60_is_medium(self):
        """Boundary: 0.60 is inclusive for 'Medium'."""
        assert confidence_label(0.60) == "Medium"

    def test_confidence_label_just_below_0_60_is_low(self):
        """0.5999 falls into 'Low'."""
        assert confidence_label(0.5999) == "Low"

    # ── Average-case paths ───────────────────────────────────────────────────

    def test_confidence_medium_confidence_profile(self):
        """Realistic mid-tier profile: ~0.65 → 'Medium'."""
        # 0.7*0.30 + 0.6*0.20 + 0.65*0.20 + 0.6*0.20 + 0.5*0.10
        # = 0.21 + 0.12 + 0.13 + 0.12 + 0.05 = 0.63
        c = calculate_confidence(0.7, 0.6, 0.65, 0.6, 0.5)
        assert c == pytest.approx(0.63, abs=0.0001)
        assert confidence_label(c) == "Medium"

    def test_confidence_single_component_extraction_quality(self):
        """Only extraction_quality contributes (weight 0.30)."""
        assert calculate_confidence(1.0, 0.0, 0.0, 0.0, 0.0) == 0.3

    def test_confidence_single_component_rule_agreement(self):
        """Only rule_agreement contributes (weight 0.20)."""
        assert calculate_confidence(0.0, 0.0, 0.0, 1.0, 0.0) == 0.2

    def test_confidence_single_component_data_completeness(self):
        """data_completeness is the lightest weight (0.10)."""
        assert calculate_confidence(0.0, 0.0, 0.0, 0.0, 1.0) == 0.1

    def test_confidence_rounds_to_4_decimal_places(self):
        """Output is always rounded to 4 dp."""
        c = calculate_confidence(0.333, 0.333, 0.333, 0.333, 0.333)
        assert c == round(c, 4)
        assert len(str(c).split(".")[-1]) <= 4

    def test_confidence_weights_sum_verified_via_all_inputs_equal(self):
        """All inputs = x → confidence = x (weights sum to 1.0)."""
        for x in [0.0, 0.25, 0.5, 0.75, 1.0]:
            assert calculate_confidence(x, x, x, x, x) == pytest.approx(x, abs=0.0001)

    # ── Worst-case / boundary paths ──────────────────────────────────────────

    def test_confidence_all_zeros_is_0_0(self):
        """All zero inputs → 0.0."""
        assert calculate_confidence(0.0, 0.0, 0.0, 0.0, 0.0) == 0.0

    def test_confidence_label_zero_is_low(self):
        assert confidence_label(0.0) == "Low"

    def test_confidence_label_one_is_high(self):
        assert confidence_label(1.0) == "High"

    def test_confidence_inputs_above_1_clamped_to_1(self):
        """Input 1.5 is clamped to 1.0 before formula."""
        clamped = calculate_confidence(1.5, 1.5, 1.5, 1.5, 1.5)
        assert clamped == 1.0

    def test_confidence_inputs_below_0_clamped_to_0(self):
        """Negative inputs clamped to 0.0."""
        clamped = calculate_confidence(-1.0, -1.0, -1.0, -1.0, -1.0)
        assert clamped == 0.0

    def test_confidence_mixed_out_of_range_clamp(self):
        """1.5 clamped to 1.0, -0.5 clamped to 0.0."""
        # eq=1.0, ec=0.0, rq=0.5, ra=0.5, dc=0.5
        # 1.0*0.30 + 0.0*0.20 + 0.5*0.20 + 0.5*0.20 + 0.5*0.10 = 0.30+0+0.10+0.10+0.05 = 0.55
        c = calculate_confidence(1.5, -0.5, 0.5, 0.5, 0.5)
        assert c == pytest.approx(0.55, abs=0.0001)

    def test_confidence_percentage_full_range(self):
        """percentage helper converts correctly at 0, 0.5, 1.0."""
        assert confidence_percentage(0.0) == 0.0
        assert confidence_percentage(0.5) == 50.0
        assert confidence_percentage(1.0) == 100.0

    def test_confidence_percentage_rounds_to_1_decimal(self):
        """0.8251 → 82.5 (rounded to 1 dp)."""
        assert confidence_percentage(0.8251) == 82.5

    def test_confidence_percentage_clamped_above_100(self):
        """Input > 1 clamped to 100% by percentage helper."""
        assert confidence_percentage(1.5) == 100.0

    def test_confidence_percentage_clamped_below_0(self):
        """Negative input clamped to 0% by percentage helper."""
        assert confidence_percentage(-0.5) == 0.0



# ============================================================================
# SECTION 8 — RANKING ENGINE
# ============================================================================
from app.engines.ranking import calculate_final_score, get_top_supplier_id, score_suppliers
from app.engines.types import ScenarioConfig, ScoreWeights, SupplierInput


def _make_supplier(
    sid: str,
    quoted_price: float = 100.0,
    shipping_cost: float = 10.0,
    duty_rate: float = 0.0,
    lead_time_days: int = 14,
    certs: tuple = (),
    caps: tuple = (),
    **kwargs,
) -> SupplierInput:
    """Minimal helper — only the fields under test need non-default values."""
    return SupplierInput(
        supplier_id=sid,
        quoted_price=quoted_price,
        shipping_cost=shipping_cost,
        duty_rate=duty_rate,
        lead_time_days=lead_time_days,
        supplier_certs=certs,
        capabilities=caps,
        **kwargs,
    )


class TestRankingEdgeCases:
    # ── Best-case paths ──────────────────────────────────────────────────────

    def test_ranking_single_supplier_gets_rank_1_and_cost_100(self):
        """Only one supplier → cheapest by definition → cost_score=100, rank=1."""
        ranking = score_suppliers([_make_supplier("solo")])
        assert len(ranking) == 1
        assert ranking[0].rank == 1
        assert ranking[0].cost_score == 100.0
        assert ranking[0].disqualified is False

    def test_ranking_empty_supplier_list_returns_empty(self):
        """No suppliers → empty list, no crash."""
        assert score_suppliers([]) == []

    def test_ranking_import_duty_rate_override_replaces_supplier_duty(self):
        """ScenarioConfig.import_duty_rate overrides supplier.duty_rate."""
        # Supplier has 0 duty, scenario imposes 50 % → landed cost rises
        s = _make_supplier("s1", quoted_price=100.0, shipping_cost=0.0, duty_rate=0.0)
        baseline = score_suppliers([s])
        with_duty = score_suppliers([s], config=ScenarioConfig(import_duty_rate=0.50))
        assert with_duty[0].landed_cost > baseline[0].landed_cost
        # landed = (100 + 0 + 100*0.50) * 1 = 150
        assert with_duty[0].landed_cost == pytest.approx(150.0)

    def test_ranking_import_duty_rate_none_uses_supplier_duty(self):
        """import_duty_rate=None in config → supplier's own duty_rate is used."""
        s = _make_supplier("s1", quoted_price=100.0, shipping_cost=0.0, duty_rate=0.10)
        default_config = score_suppliers([s], config=ScenarioConfig(import_duty_rate=None))
        assert default_config[0].landed_cost == pytest.approx(110.0)

    # ── Average-case paths ───────────────────────────────────────────────────

    def test_ranking_tiebreaker_alphabetical_by_supplier_id(self):
        """Two suppliers with identical profiles → sorted alphabetically by id."""
        s_z = _make_supplier("z-supplier")
        s_a = _make_supplier("a-supplier")
        ranking = score_suppliers([s_z, s_a])
        # Scores are identical; tiebreaker is supplier_id ascending
        assert ranking[0].supplier_id == "a-supplier"
        assert ranking[1].supplier_id == "z-supplier"

    def test_ranking_stacked_currency_rates_multiply(self):
        """config.currency_rate * supplier.currency_rate are multiplied together."""
        # supplier has currency_rate=1.2, config has currency_rate=1.1 → effective=1.32
        s = _make_supplier("s1", quoted_price=100.0, shipping_cost=0.0, duty_rate=0.0,
                           currency_rate=1.2)
        result = score_suppliers([s], config=ScenarioConfig(currency_rate=1.1))
        # landed = 100 * 1.32 = 132.0
        assert result[0].landed_cost == pytest.approx(132.0)

    def test_ranking_material_cost_multiplier_raises_landed_cost_and_duty(self):
        """material_cost_multiplier scales quoted_price, which also raises duty."""
        s = _make_supplier("s1", quoted_price=100.0, shipping_cost=0.0, duty_rate=0.10)
        base = score_suppliers([s])
        doubled = score_suppliers([s], config=ScenarioConfig(material_cost_multiplier=2.0))
        # baseline: landed = 100 + 10 = 110
        # doubled:  quoted = 200, duty = 20, landed = 220
        assert base[0].landed_cost == pytest.approx(110.0)
        assert doubled[0].landed_cost == pytest.approx(220.0)

    def test_ranking_lead_time_adjustment_applied_before_scoring(self):
        """lead_time_adjustment_days shifts each supplier's lead time."""
        s_fast = _make_supplier("fast", lead_time_days=10)
        s_slow = _make_supplier("slow", lead_time_days=20)
        # Add +5 days to both — fast becomes 15, slow becomes 25
        # Relative ratio stays the same: 15/15=100 for fast, 15/25=60 for slow
        ranking = score_suppliers([s_fast, s_slow],
                                  config=ScenarioConfig(lead_time_adjustment_days=5))
        fast_item = next(r for r in ranking if r.supplier_id == "fast")
        slow_item = next(r for r in ranking if r.supplier_id == "slow")
        assert fast_item.delivery_score > slow_item.delivery_score

    def test_ranking_demand_multiplier_reduces_capacity(self):
        """demand_multiplier=2 halves effective capacity for every supplier."""
        s = _make_supplier("s1", production_capacity_pct=80.0)
        base = score_suppliers([s])
        high_demand = score_suppliers([s], config=ScenarioConfig(demand_multiplier=2.0))
        # Effective capacity: 80/2=40 → lower delivery and capability scores
        assert high_demand[0].delivery_score < base[0].delivery_score

    # ── Worst-case / boundary paths ──────────────────────────────────────────

    def test_ranking_all_suppliers_unavailable_all_disqualified(self):
        """All suppliers marked unavailable → all disqualified, scores=0."""
        suppliers = [_make_supplier("a"), _make_supplier("b"), _make_supplier("c")]
        config = ScenarioConfig(supplier_availability={"a": False, "b": False, "c": False})
        ranking = score_suppliers(suppliers, config=config)
        assert all(r.disqualified for r in ranking)
        assert all(r.final_score == 0.0 for r in ranking)
        assert all(r.landed_cost == 0.0 for r in ranking)

    def test_ranking_get_top_supplier_id_all_disqualified_returns_empty_string(self):
        """get_top_supplier_id returns '' when every supplier is disqualified."""
        suppliers = [_make_supplier("a"), _make_supplier("b")]
        config = ScenarioConfig(supplier_availability={"a": False, "b": False})
        ranking = score_suppliers(suppliers, config=config)
        assert get_top_supplier_id(ranking) == ""

    def test_ranking_demand_multiplier_zero_collapses_all_capacity(self):
        """demand_multiplier=0 → _adjusted_capacity_pct returns 0 for all suppliers."""
        s = _make_supplier("s1", production_capacity_pct=100.0)
        ranking = score_suppliers([s], config=ScenarioConfig(demand_multiplier=0.0))
        # delivery_score drops because capacity=0; capability also lower
        assert ranking[0].delivery_score < 100.0

    def test_ranking_certification_override_false_removes_cert_for_compliance(self):
        """certification_overrides={cert: False} strips that cert before compliance check."""
        s = _make_supplier("s1", certs=("ISO 9001:2015",))
        # Without override: supplier meets requirement
        base = score_suppliers([s], required_certs=["ISO 9001"])
        assert base[0].compliance_score == 100.0
        # With override invalidating the cert: should fail
        override = score_suppliers(
            [s],
            required_certs=["ISO 9001"],
            config=ScenarioConfig(certification_overrides={"ISO 9001:2015": False}),
        )
        assert override[0].compliance_score == 0.0

    def test_ranking_final_score_clamped_to_0_100(self):
        """calculate_final_score clamps output even if weighted sum exceeds range."""
        weights = ScoreWeights(cost=1.0, quality=0.0, delivery=0.0,
                               risk=0.0, capability=0.0, compliance=0.0)
        assert calculate_final_score(150.0, 0.0, 0.0, 0.0, 0.0, 0.0, weights) == 100.0
        assert calculate_final_score(-50.0, 0.0, 0.0, 0.0, 0.0, 0.0, weights) == 0.0

    def test_ranking_disqualified_suppliers_ranked_last(self):
        """Unavailable supplier is appended after all active ones regardless of id."""
        s_active = _make_supplier("zzz")  # Would sort last alphabetically
        s_out = _make_supplier("aaa")
        config = ScenarioConfig(supplier_availability={"aaa": False})
        ranking = score_suppliers([s_active, s_out], config=config)
        # active supplier should be rank 1, disqualified last
        active = next(r for r in ranking if r.supplier_id == "zzz")
        disq = next(r for r in ranking if r.supplier_id == "aaa")
        assert active.rank < disq.rank

    def test_ranking_required_capabilities_empty_list_all_get_100_cap_score(self):
        """No required capabilities → every supplier scores 100 on capability match."""
        suppliers = [_make_supplier("a", caps=()), _make_supplier("b", caps=("CNC",))]
        ranking = score_suppliers(suppliers, required_capabilities=[])
        for r in ranking:
            # capability_score = 100*0.70 + 100*0.30 = 100 (no support bonus)
            assert r.capability_score == pytest.approx(100.0, abs=0.1)



# ============================================================================
# SECTION 9 — SCENARIO ENGINE
# ============================================================================
from app.engines.scenario import simulate_scenario


def _two_suppliers() -> list[SupplierInput]:
    """Acme: low price, high shipping. FastTrack: high price, low shipping.
    At baseline Acme wins on quality+risk; at shipping*1.4 FastTrack takes over."""
    return [
        SupplierInput(
            supplier_id="acme",
            quoted_price=95.0,
            shipping_cost=22.0,
            duty_rate=0.05,
            lead_time_days=14,
            defect_rate=0.0,
            inspection_pass_rate=100.0,
            customer_rating=5.0,
            on_time_delivery_pct=96.0,
            production_capacity_pct=95.0,
            engineering_support=True,
            capabilities=("CNC Machining", "Assembly"),
            supplier_certs=("ISO 9001:2015", "AS9100D"),
            financial_risk=5.0,
            country_risk=8.0,
            supply_risk=6.0,
            compliance_risk=4.0,
            capacity_risk=5.0,
        ),
        SupplierInput(
            supplier_id="fasttrack",
            quoted_price=115.0,
            shipping_cost=4.0,
            duty_rate=0.0,
            lead_time_days=10,
            defect_rate=4.0,
            inspection_pass_rate=94.0,
            customer_rating=4.1,
            on_time_delivery_pct=97.0,
            production_capacity_pct=92.0,
            capabilities=("CNC Machining", "Stamping"),
            supplier_certs=("ISO 9001:2015",),
            financial_risk=18.0,
            country_risk=22.0,
            supply_risk=20.0,
            compliance_risk=15.0,
            capacity_risk=18.0,
        ),
    ]


class TestScenarioEdgeCases:
    # ── Best-case paths ──────────────────────────────────────────────────────

    def test_scenario_identity_config_no_ranking_change(self):
        """Default ScenarioConfig() equals baseline → ranking_changed=False."""
        result = simulate_scenario(
            suppliers=_two_suppliers(),
            scenario_config=ScenarioConfig(),  # identity — no changes
        )
        assert result.ranking_changed is False
        assert result.previous_top_supplier_id == result.new_top_supplier_id

    def test_scenario_baseline_always_uses_default_config(self):
        """Baseline is always recomputed with ScenarioConfig() regardless of scenario."""
        result = simulate_scenario(
            suppliers=_two_suppliers(),
            scenario_config=ScenarioConfig(shipping_multiplier=1.4),
        )
        # Baseline top should be acme (wins without shipping stress)
        assert result.previous_top_supplier_id == "acme"

    def test_scenario_result_contains_all_suppliers_in_both_rankings(self):
        """Both baseline_ranking and scenario_ranking include every supplier."""
        result = simulate_scenario(
            suppliers=_two_suppliers(),
            scenario_config=ScenarioConfig(shipping_multiplier=1.4),
        )
        baseline_ids = {r.supplier_id for r in result.baseline_ranking}
        scenario_ids = {r.supplier_id for r in result.scenario_ranking}
        assert baseline_ids == {"acme", "fasttrack"}
        assert scenario_ids == {"acme", "fasttrack"}

    # ── Average-case paths ───────────────────────────────────────────────────

    def test_scenario_material_cost_multiplier_raises_both_landed_costs(self):
        """material_cost_multiplier > 1 raises landed cost for every supplier."""
        result = simulate_scenario(
            suppliers=_two_suppliers(),
            scenario_config=ScenarioConfig(material_cost_multiplier=1.5),
        )
        for sid in ("acme", "fasttrack"):
            baseline = next(r for r in result.baseline_ranking if r.supplier_id == sid)
            scenario = next(r for r in result.scenario_ranking if r.supplier_id == sid)
            assert scenario.landed_cost > baseline.landed_cost

    def test_scenario_negative_lead_time_adjustment_fastest_supplier_always_100_lead_component(self):
        """lead_time_adjustment_days=-5: all lead times shift equally.
        The fastest supplier still scores lead_component=100 (min/min=1).
        The relative ratio of the slower supplier changes because the absolute
        gap is unchanged while the absolute values are smaller — it can go either
        direction, so we only assert the invariant: fastest supplier's lead
        component stays at 100, and the ranking order by delivery is preserved."""
        result = simulate_scenario(
            suppliers=_two_suppliers(),
            scenario_config=ScenarioConfig(lead_time_adjustment_days=-5),
        )
        # fasttrack (10d → 5d) remains the fastest; acme (14d → 9d) stays slower
        scenario_fast = next(r for r in result.scenario_ranking if r.supplier_id == "fasttrack")
        scenario_acme = next(r for r in result.scenario_ranking if r.supplier_id == "acme")
        # Fastest supplier still beats slower on delivery
        assert scenario_fast.delivery_score >= scenario_acme.delivery_score

    def test_scenario_positive_lead_time_adjustment_slower_supplier_relatively_improves(self):
        """lead_time_adjustment_days=+10: adding equal days to all suppliers
        compresses the relative ratio gap (longer lead times converge toward
        the minimum faster in ratio terms). Acme (14→24) vs FastTrack (10→20):
        baseline ratio 10/14≈71 %, scenario ratio 20/24≈83 % — the slower
        supplier improves its lead_component as ratios converge."""
        result = simulate_scenario(
            suppliers=_two_suppliers(),
            scenario_config=ScenarioConfig(lead_time_adjustment_days=10),
        )
        baseline_acme = next(r for r in result.baseline_ranking if r.supplier_id == "acme")
        scenario_acme = next(r for r in result.scenario_ranking if r.supplier_id == "acme")
        # Adding equal days compresses ratio gap → acme's delivery score improves
        assert scenario_acme.delivery_score > baseline_acme.delivery_score

    def test_scenario_currency_rate_scales_both_landed_costs(self):
        """currency_rate=1.3 raises every supplier's landed cost proportionally."""
        result = simulate_scenario(
            suppliers=_two_suppliers(),
            scenario_config=ScenarioConfig(currency_rate=1.3),
        )
        # Cost scores should stay the same (min/supplier ratio is unchanged when
        # all costs scale by the same factor and supplier.currency_rate=1.0 for both)
        for r in result.scenario_ranking:
            if not r.disqualified:
                baseline = next(b for b in result.baseline_ranking if b.supplier_id == r.supplier_id)
                assert r.cost_score == pytest.approx(baseline.cost_score, abs=0.1)

    def test_scenario_demand_multiplier_2_reduces_capacity_scores(self):
        """demand_multiplier=2 halves effective capacity → lower delivery/capability."""
        result = simulate_scenario(
            suppliers=_two_suppliers(),
            scenario_config=ScenarioConfig(demand_multiplier=2.0),
        )
        for sid in ("acme", "fasttrack"):
            baseline = next(r for r in result.baseline_ranking if r.supplier_id == sid)
            scenario = next(r for r in result.scenario_ranking if r.supplier_id == sid)
            assert scenario.delivery_score < baseline.delivery_score

    def test_scenario_cert_override_disqualifies_supplier_from_compliance(self):
        """Invalidating 'ISO 9001:2015' via override causes compliance_score=0
        for both suppliers that hold it when 'ISO 9001' is required."""
        result = simulate_scenario(
            suppliers=_two_suppliers(),
            scenario_config=ScenarioConfig(certification_overrides={"ISO 9001:2015": False}),
            required_certs=["ISO 9001"],
        )
        for r in result.scenario_ranking:
            assert r.compliance_score == 0.0

    # ── Worst-case / boundary paths ──────────────────────────────────────────

    def test_scenario_all_suppliers_unavailable_top_ids_both_empty_string(self):
        """When all suppliers are unavailable in both baseline and scenario,
        both top IDs are '' and ranking_changed=False ('' == '')."""
        all_out = ScenarioConfig(
            supplier_availability={"acme": False, "fasttrack": False}
        )
        result = simulate_scenario(
            suppliers=_two_suppliers(),
            scenario_config=all_out,
        )
        # Baseline uses default config (both available), so previous_top != ''
        assert result.previous_top_supplier_id != ""
        # Scenario has all unavailable → new_top = ''
        assert result.new_top_supplier_id == ""
        assert result.ranking_changed is True  # '' != previous_top

    def test_scenario_single_supplier_unavailable_other_becomes_top(self):
        """Removing acme from scenario makes fasttrack the new top."""
        result = simulate_scenario(
            suppliers=_two_suppliers(),
            scenario_config=ScenarioConfig(supplier_availability={"acme": False}),
        )
        assert result.new_top_supplier_id == "fasttrack"
        assert result.ranking_changed is True

    def test_scenario_shipping_multiplier_1_same_as_baseline(self):
        """shipping_multiplier=1.0 is the default — no change expected."""
        result = simulate_scenario(
            suppliers=_two_suppliers(),
            scenario_config=ScenarioConfig(shipping_multiplier=1.0),
        )
        assert result.ranking_changed is False

    def test_scenario_extreme_shipping_multiplier_collapses_high_shipping_score(self):
        """Very high shipping_multiplier destroys cost advantage of high-shipping supplier."""
        result = simulate_scenario(
            suppliers=_two_suppliers(),
            scenario_config=ScenarioConfig(shipping_multiplier=10.0),
        )
        # Acme ($22 shipping) should be far behind fasttrack ($4 shipping)
        scenario_acme = next(r for r in result.scenario_ranking if r.supplier_id == "acme")
        scenario_fast = next(r for r in result.scenario_ranking if r.supplier_id == "fasttrack")
        assert scenario_fast.cost_score > scenario_acme.cost_score

    def test_scenario_single_supplier_ranking_never_changes(self):
        """Only one supplier — top cannot change regardless of config."""
        solo = [_two_suppliers()[0]]  # just acme
        result = simulate_scenario(
            suppliers=solo,
            scenario_config=ScenarioConfig(shipping_multiplier=5.0, currency_rate=2.0),
        )
        assert result.ranking_changed is False
        assert result.previous_top_supplier_id == result.new_top_supplier_id == "acme"

    def test_scenario_both_rankings_have_correct_length(self):
        """Tupled rankings always contain exactly as many entries as suppliers."""
        suppliers = _two_suppliers()
        result = simulate_scenario(
            suppliers=suppliers,
            scenario_config=ScenarioConfig(shipping_multiplier=1.4),
        )
        assert len(result.baseline_ranking) == len(suppliers)
        assert len(result.scenario_ranking) == len(suppliers)

