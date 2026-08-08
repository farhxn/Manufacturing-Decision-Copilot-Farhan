from app.engines.ranking import calculate_final_score, score_suppliers
from app.engines.types import ScoreWeights, SupplierInput


def _demo_suppliers() -> list[SupplierInput]:
    # acme: lower quoted_price (95) than fasttrack (115) but higher shipping (22 vs 4).
    # At baseline acme wins on quality + risk + compliance.
    # At shipping*1.4 acme's landed cost rises more than fasttrack's, flipping the ranking.
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
        SupplierInput(
            supplier_id="global-fab",
            quoted_price=89.0,
            shipping_cost=35.0,
            duty_rate=0.25,
            lead_time_days=28,
            defect_rate=6.0,
            inspection_pass_rate=90.0,
            customer_rating=3.9,
            on_time_delivery_pct=88.0,
            production_capacity_pct=85.0,
            capabilities=("Injection Molding",),
            supplier_certs=("ISO 9001:2015",),
            financial_risk=30.0,
            country_risk=35.0,
            supply_risk=32.0,
            compliance_risk=25.0,
            capacity_risk=28.0,
        ),
    ]


def test_ranking_orders_by_final_score_descending():
    ranking = score_suppliers(
        _demo_suppliers(),
        required_certs=["ISO 9001"],
        required_capabilities=["CNC Machining"],
    )

    assert len(ranking) == 3
    assert ranking[0].rank == 1
    assert ranking[0].final_score >= ranking[1].final_score >= ranking[2].final_score


def test_ranking_baseline_prefers_acme_for_quality_and_risk():
    ranking = score_suppliers(
        _demo_suppliers(),
        required_certs=["ISO 9001"],
        required_capabilities=["CNC Machining"],
    )

    assert ranking[0].supplier_id == "acme"
    assert ranking[0].quality_score > ranking[1].quality_score
    assert ranking[0].risk_score > ranking[1].risk_score


def test_ranking_disqualifies_missing_compliance():
    ranking = score_suppliers(
        _demo_suppliers(),
        required_certs=["ISO 9001", "AS9100D"],
        required_capabilities=["CNC Machining"],
    )

    non_compliant = next(item for item in ranking if item.supplier_id == "fasttrack")
    assert non_compliant.compliance_score == 0.0


def test_calculate_final_score_uses_weights():
    # cost=0.50, others=0.10 each (sums to 1.0)
    # 80*0.50 + 90*0.10 + 70*0.10 + 85*0.10 + 75*0.10 + 100*0.10
    # = 40.0 + 9.0 + 7.0 + 8.5 + 7.5 + 10.0 = 82.0
    weights = ScoreWeights(
        cost=0.50,
        quality=0.10,
        delivery=0.10,
        risk=0.10,
        capability=0.10,
        compliance=0.10,
    )
    final_score = calculate_final_score(
        cost_score=80.0,
        quality_score=90.0,
        delivery_score=70.0,
        risk_score=85.0,
        capability_score=75.0,
        compliance_score=100.0,
        weights=weights,
    )
    assert final_score == 82.0


def test_ranking_is_deterministic():
    suppliers = _demo_suppliers()
    first = score_suppliers(suppliers)
    second = score_suppliers(suppliers)
    assert [(item.supplier_id, item.final_score) for item in first] == [
        (item.supplier_id, item.final_score) for item in second
    ]
