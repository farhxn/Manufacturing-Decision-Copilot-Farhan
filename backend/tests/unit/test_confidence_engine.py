from app.engines.confidence import (
    calculate_confidence,
    confidence_label,
    confidence_percentage,
)


def test_confidence_formula_weights():
    confidence = calculate_confidence(
        extraction_quality=1.0,
        evidence_coverage=1.0,
        retrieval_quality=1.0,
        rule_agreement=1.0,
        data_completeness=1.0,
    )
    assert confidence == 1.0


def test_confidence_all_zero_inputs():
    # All zero → confidence is 0.0
    confidence = calculate_confidence(
        extraction_quality=0.0,
        evidence_coverage=0.0,
        retrieval_quality=0.0,
        rule_agreement=0.0,
        data_completeness=0.0,
    )
    assert confidence == 0.0


def test_confidence_extraction_quality_weight():
    # Only extraction_quality set to 1.0; weight=0.30
    confidence = calculate_confidence(
        extraction_quality=1.0,
        evidence_coverage=0.0,
        retrieval_quality=0.0,
        rule_agreement=0.0,
        data_completeness=0.0,
    )
    assert confidence == 0.3


def test_confidence_data_completeness_weight():
    # Only data_completeness set; weight=0.10
    confidence = calculate_confidence(
        extraction_quality=0.0,
        evidence_coverage=0.0,
        retrieval_quality=0.0,
        rule_agreement=0.0,
        data_completeness=1.0,
    )
    assert confidence == 0.1


def test_confidence_partial_inputs():
    # 0.9*0.30 + 0.8*0.20 + 0.85*0.20 + 0.75*0.20 + 0.7*0.10
    # = 0.27 + 0.16 + 0.17 + 0.15 + 0.07 = 0.82
    confidence = calculate_confidence(
        extraction_quality=0.9,
        evidence_coverage=0.8,
        retrieval_quality=0.85,
        rule_agreement=0.75,
        data_completeness=0.7,
    )
    assert confidence == 0.82


def test_confidence_clamps_out_of_range_inputs():
    # extraction_quality=1.5 -> clamped to 1.0, evidence_coverage=-0.2 -> clamped to 0.0
    # 1.0*0.30 + 0.0*0.20 + 0.5*0.20 + 0.5*0.20 + 0.5*0.10
    # = 0.30 + 0.00 + 0.10 + 0.10 + 0.05 = 0.55
    confidence = calculate_confidence(
        extraction_quality=1.5,
        evidence_coverage=-0.2,
        retrieval_quality=0.5,
        rule_agreement=0.5,
        data_completeness=0.5,
    )
    assert confidence == 0.55


def test_confidence_is_deterministic():
    inputs = {
        "extraction_quality": 0.92,
        "evidence_coverage": 0.88,
        "retrieval_quality": 0.90,
        "rule_agreement": 0.86,
        "data_completeness": 0.95,
    }
    assert calculate_confidence(**inputs) == calculate_confidence(**inputs)


def test_confidence_label_thresholds():
    assert confidence_label(0.85) == "High"
    assert confidence_label(0.80) == "High"
    assert confidence_label(0.79) == "Medium"
    assert confidence_label(0.60) == "Medium"
    assert confidence_label(0.59) == "Low"


def test_confidence_percentage():
    assert confidence_percentage(0.825) == 82.5
