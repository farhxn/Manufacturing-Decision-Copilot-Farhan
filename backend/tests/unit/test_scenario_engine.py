from app.engines.scenario import simulate_scenario
from app.engines.types import ScenarioConfig, SupplierInput


def _demo_suppliers() -> list[SupplierInput]:
    # acme: lower quoted_price (95) but higher shipping (22 vs 4).
    # Baseline: acme wins on quality + risk + compliance.
    # Shipping*1.4 raises acme's landed cost more, tipping the ranking to fasttrack.
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


def test_scenario_shipping_multiplier_changes_top_supplier():
    result = simulate_scenario(
        suppliers=_demo_suppliers(),
        scenario_config=ScenarioConfig(shipping_multiplier=1.4),
        required_certs=["ISO 9001"],
        required_capabilities=["CNC Machining"],
    )

    assert result.previous_top_supplier_id == "acme"
    assert result.new_top_supplier_id == "fasttrack"
    assert result.ranking_changed is True


def test_scenario_shipping_multiplier_reduces_high_shipping_cost_score():
    result = simulate_scenario(
        suppliers=_demo_suppliers(),
        scenario_config=ScenarioConfig(shipping_multiplier=1.4),
    )

    baseline_acme = next(
        item for item in result.baseline_ranking if item.supplier_id == "acme"
    )
    scenario_acme = next(
        item for item in result.scenario_ranking if item.supplier_id == "acme"
    )

    assert scenario_acme.cost_score < baseline_acme.cost_score
    assert scenario_acme.landed_cost > baseline_acme.landed_cost


def test_scenario_removes_unavailable_supplier():
    result = simulate_scenario(
        suppliers=_demo_suppliers(),
        scenario_config=ScenarioConfig(supplier_availability={"acme": False}),
    )

    removed = next(item for item in result.scenario_ranking if item.supplier_id == "acme")
    assert removed.disqualified is True
    assert removed.final_score == 0.0
    assert result.new_top_supplier_id == "fasttrack"


def test_scenario_currency_change_affects_landed_cost():
    result = simulate_scenario(
        suppliers=_demo_suppliers(),
        scenario_config=ScenarioConfig(currency_rate=1.2),
    )

    baseline_acme = next(
        item for item in result.baseline_ranking if item.supplier_id == "acme"
    )
    scenario_acme = next(
        item for item in result.scenario_ranking if item.supplier_id == "acme"
    )

    assert scenario_acme.landed_cost > baseline_acme.landed_cost


def test_scenario_certification_override_can_disqualify_supplier():
    result = simulate_scenario(
        suppliers=_demo_suppliers(),
        scenario_config=ScenarioConfig(certification_overrides={"ISO 9001:2015": False}),
        required_certs=["ISO 9001"],
    )

    scenario_acme = next(
        item for item in result.scenario_ranking if item.supplier_id == "acme"
    )
    assert scenario_acme.compliance_score == 0.0
