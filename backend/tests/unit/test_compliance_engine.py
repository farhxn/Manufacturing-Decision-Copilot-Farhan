import pytest
from app.engines.compliance import calculate_compliance_score


def test_compliance_score_no_requirements():
    # No required certs → always fully compliant
    score = calculate_compliance_score(
        supplier_certs=["ISO 9001"],
        required_certs=[],
    )
    assert score == 100.0


def test_compliance_score_both_lists_empty():
    # Both lists empty → fully compliant (no requirements to fail)
    score = calculate_compliance_score(
        supplier_certs=[],
        required_certs=[],
    )
    assert score == 100.0


def test_compliance_score_all_met():
    # Case-insensitive: lowercase requirement matches mixed-case cert
    score = calculate_compliance_score(
        supplier_certs=["ISO 9001", "RoHS", "AS9100D"],
        required_certs=["iso 9001", "rohs"],
    )
    assert score == 100.0


def test_compliance_score_missing_one():
    # Missing one mandatory cert → disqualified (score 0)
    score = calculate_compliance_score(
        supplier_certs=["ISO 9001"],
        required_certs=["ISO 9001", "RoHS"],
    )
    assert score == 0.0


def test_compliance_score_empty_supplier_certs():
    # Supplier holds no certs but one is required → disqualified
    score = calculate_compliance_score(
        supplier_certs=[],
        required_certs=["ISO 9001"],
    )
    assert score == 0.0


def test_compliance_score_prefix_colon_match():
    # "ISO 9001" should match the versioned cert "ISO 9001:2015"
    score = calculate_compliance_score(
        supplier_certs=["ISO 9001:2015", "AS9100D"],
        required_certs=["ISO 9001"],
    )
    assert score == 100.0


def test_compliance_score_prefix_space_match():
    # "ISO 9001" should match "ISO 9001 Certified" (space boundary)
    score = calculate_compliance_score(
        supplier_certs=["ISO 9001 Certified"],
        required_certs=["ISO 9001"],
    )
    assert score == 100.0


def test_compliance_score_prefix_too_broad_does_not_match():
    # "ISO" alone must NOT match "ISO 9001:2015" — prefix boundary enforced
    score = calculate_compliance_score(
        supplier_certs=["ISO 9001:2015"],
        required_certs=["ISO"],
    )
    assert score == 0.0


def test_compliance_score_rohs_versioned_match():
    # "RoHS" requirement satisfied by "RoHS Compliant" (space boundary)
    score = calculate_compliance_score(
        supplier_certs=["RoHS Compliant", "ISO 9001:2015"],
        required_certs=["RoHS"],
    )
    assert score == 100.0


def test_compliance_score_multiple_required_one_fails():
    # Three required, supplier missing AS9100D → zero
    score = calculate_compliance_score(
        supplier_certs=["ISO 9001:2015", "RoHS"],
        required_certs=["ISO 9001", "RoHS", "AS9100D"],
    )
    assert score == 0.0


def test_compliance_score_whitespace_in_requirement_stripped():
    # Leading/trailing whitespace in requirement name is stripped before matching
    score = calculate_compliance_score(
        supplier_certs=["ISO 9001:2015"],
        required_certs=["  ISO 9001  "],
    )
    assert score == 100.0
