"""
Phase 7 smoke tests — run without a database or live services.
Verifies: reports route registered, schemas importable + instantiable,
repository importable, service importable, route handler structure,
standard envelope shape, and OpenAPI documents the new paths.

Usage:
    cd backend
    python tests/smoke_phase7.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


# ── 1. Report schemas importable and instantiable ────────────────────────────

def test_report_schemas() -> None:
    from app.schemas.report import (
        ReportGenerateRequest,
        ReportSummarySchema,
        ReportDetailSchema,
        ReportDownloadSchema,
    )
    from datetime import datetime, timezone

    now = datetime.now(timezone.utc)

    req = ReportGenerateRequest(
        project_id="00000000-0000-4000-a000-000000000002",
        report_type="executive",
        title=None,
    )
    assert req.report_type == "executive"
    assert req.project_id == "00000000-0000-4000-a000-000000000002"

    summary = ReportSummarySchema(
        id="rep-001",
        title="Q4 Motor Housing Report",
        report_type="executive",
        project_id="00000000-0000-4000-a000-000000000002",
        created_at=now,
    )
    assert summary.id == "rep-001"

    detail = ReportDetailSchema(
        id="rep-001",
        title="Q4 Motor Housing Report",
        report_type="executive",
        project_id="00000000-0000-4000-a000-000000000002",
        created_at=now,
        summary_text="Acme Precision is recommended.\n═══\nRanking: #1 Acme",
    )
    assert "Acme" in detail.summary_text

    dl = ReportDownloadSchema(
        id="rep-001",
        title="Q4 Motor Housing Report",
        content="MANUFACTURING DECISION COPILOT\n...",
        filename="MDC_Report_Q4_Motor_Housing_Report_rep-001.txt",
    )
    assert dl.filename.endswith(".txt")
    assert dl.content.startswith("MANUFACTURING DECISION COPILOT")

    print("  report schemas  OK")


# ── 2. Repository importable ──────────────────────────────────────────────────

def test_report_repository() -> None:
    from app.repositories.report_repository import ReportRepository
    # Verify the four public methods exist
    for method in ("create", "get_by_id", "list_by_project", "delete"):
        assert hasattr(ReportRepository, method), f"ReportRepository missing method: {method}"
    print("  ReportRepository importable  OK")


# ── 3. Service importable and _build_report_text works offline ───────────────

def test_report_service() -> None:
    from app.services.report_service import ReportService, _build_report_text

    # Construct a minimal RecommendationSchema-like object
    from app.schemas.recommendation import RecommendationSchema, RankedSupplierSchema
    from app.schemas.supplier import SupplierScoreSchema

    scores = SupplierScoreSchema(
        cost_score=88.0,
        quality_score=92.0,
        delivery_score=85.0,
        risk_score=90.0,
        capability_score=80.0,
        compliance_score=100.0,
        final_score=89.5,
        rank=1,
        landed_cost=121.75,
    )
    ranked = RankedSupplierSchema(
        supplier_id="sup-1",
        supplier_name="Acme Precision Mfg",
        country="Germany",
        rank=1,
        final_score=89.5,
        lead_time_days=14,
        scores=scores,
    )
    rec = RecommendationSchema(
        project_id="00000000-0000-4000-a000-000000000002",
        recommended_supplier_id="sup-1",
        recommended_supplier_name="Acme Precision Mfg",
        summary="Acme is top-ranked based on quality and compliance.",
        confidence_score=84.2,
        confidence_label="High",
        confidence_explanation="3/3 complete profiles; 5 supporting documents.",
        ranking=[ranked],
        pros=["ISO 9001:2015 certified", "Low defect rate < 0.1%"],
        cons=["Higher landed cost vs. FastTrack"],
        tradeoffs=["Cost premium justified by quality margin"],
        risks=["Capacity risk in Q4 peak season"],
        assumptions=["Pricing current as of Q4 2026"],
        limitations=["Only 5 documents analysed"],
        next_actions=["Issue RFQ", "Request Certificate of Conformance"],
        evidence_ids=["chunk-001", "chunk-002"],
        ai_narrative=True,
    )

    text = _build_report_text(
        project_name="Motor Housing Sourcing Project",
        report_type="executive",
        rec=rec,
        generated_at="2026-08-09 12:00 UTC",
    )

    # Structural checks
    assert "MANUFACTURING DECISION COPILOT" in text
    assert "Acme Precision Mfg" in text
    assert "84.2%" in text, f"Confidence line missing. Got:\n{text[:300]}"
    assert "SUPPLIER RANKING" in text
    assert "#" in text                              # rank column
    assert "STRENGTHS" in text
    assert "RISKS" in text
    assert "NEXT ACTIONS" in text
    assert "DISCLAIMER" in text

    line_count = text.count("\n")
    assert line_count >= 20, f"Report suspiciously short: {line_count} lines"

    print(f"  _build_report_text OK  ({line_count} lines, {len(text)} chars)")
    print("  ReportService importable  OK")


# ── 4. Routes registered ──────────────────────────────────────────────────────

def test_routes_registered() -> None:
    from app.main import app

    paths = {r.path for r in app.routes if hasattr(r, "path")}

    expected = {
        "/api/v1/reports/generate",
        "/api/v1/reports",
        "/api/v1/reports/{report_id}/download",
        "/api/v1/reports/{report_id}",
    }
    missing = expected - paths
    assert not missing, f"Missing report routes: {missing}"
    print(f"  All {len(expected)} Phase 7 routes registered  OK")


# ── 5. OpenAPI documents the new paths ───────────────────────────────────────

def test_openapi_schema() -> None:
    from app.main import app

    schema = app.openapi()
    report_paths = [p for p in schema["paths"] if "reports" in p]
    assert len(report_paths) >= 3, (
        f"Expected ≥3 report paths in OpenAPI, got {len(report_paths)}: {report_paths}"
    )
    print(f"  OpenAPI schema OK — {len(report_paths)} report paths documented")


# ── 6. Dependency wired (get_report_service importable) ──────────────────────

def test_dependency_wired() -> None:
    from app.core.dependencies import get_report_service
    import inspect

    assert inspect.isasyncgenfunction(get_report_service), (
        "get_report_service should be an async generator function"
    )
    print("  get_report_service dependency wired  OK")


# ── 7. Standard envelope shape ────────────────────────────────────────────────

def test_standard_envelope() -> None:
    from app.schemas.common import APIResponse
    from app.schemas.report import ReportSummarySchema
    from datetime import datetime, timezone

    summaries = [
        ReportSummarySchema(
            id=f"rep-00{i}",
            title=f"Report {i}",
            report_type="executive",
            project_id="00000000-0000-4000-a000-000000000002",
            created_at=datetime.now(timezone.utc),
        )
        for i in range(3)
    ]
    env = APIResponse(success=True, message="3 report(s) retrieved.", data=summaries, meta=None)
    dumped = env.model_dump()
    for field in ("success", "message", "data", "meta"):
        assert field in dumped, f"Envelope missing field: {field}"
    assert len(dumped["data"]) == 3
    print("  standard envelope with ReportSummarySchema  OK")


# ── Runner ────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("\n=== Phase 7 Smoke Tests ===\n")

    tests = [
        ("report_schemas",       test_report_schemas),
        ("report_repository",    test_report_repository),
        ("report_service",       test_report_service),
        ("routes_registered",    test_routes_registered),
        ("openapi_schema",       test_openapi_schema),
        ("dependency_wired",     test_dependency_wired),
        ("standard_envelope",    test_standard_envelope),
    ]

    passed = failed = 0
    for name, fn in tests:
        try:
            print(f"[{name}]")
            fn()
            passed += 1
        except Exception as exc:
            print(f"  FAILED: {exc}")
            failed += 1

    print(f"\n{'-' * 40}")
    print(f"Results: {passed} passed, {failed} failed")
    if failed:
        sys.exit(1)
    print("Phase 7 smoke tests PASSED")
