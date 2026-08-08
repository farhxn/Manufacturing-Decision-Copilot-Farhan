"""
Phase 4 smoke tests — run without a database or live services.
Verifies: routes registered, schemas importable + instantiable,
repositories importable, services importable, standard envelope shape.

Usage:
    cd backend
    python tests/smoke_phase4.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


# ── 1. Route registration ────────────────────────────────────────────────────

def test_routes_registered() -> None:
    from app.main import app

    paths = {r.path for r in app.routes if hasattr(r, "path")}

    expected = {
        # Suppliers
        "/api/v1/suppliers",
        "/api/v1/suppliers/{supplier_id}",
        "/api/v1/suppliers/compare",
        # Recommendations
        "/api/v1/recommendations",
        "/api/v1/recommendations/regenerate",
        # Scenarios
        "/api/v1/scenarios",
        "/api/v1/scenarios/{scenario_id}",
        "/api/v1/scenarios/{scenario_id}/simulate",
        # Dashboard
        "/api/v1/dashboard",
        # Evidence
        "/api/v1/evidence/{recommendation_id}",
    }

    missing = expected - paths
    assert not missing, f"Missing routes: {missing}"
    print(f"  All {len(expected)} Phase 4 routes registered  OK")


# ── 2. Schemas importable and instantiable ───────────────────────────────────

def test_schemas() -> None:
    # common
    from app.schemas.common import APIResponse, PaginationMeta

    meta = PaginationMeta(page=1, limit=20, total=5, pages=1)
    assert meta.total == 5

    env = APIResponse(success=True, message="ok", data={"x": 1}, meta=None)
    assert env.success is True
    print("  common schemas  OK")

    # supplier
    from app.schemas.supplier import (
        SupplierCompareRequest,
        SupplierDetailSchema,
        SupplierSummarySchema,
    )
    print("  supplier schemas importable  OK")

    # recommendation
    from app.schemas.recommendation import RecommendationSchema
    print("  recommendation schema importable  OK")

    # scenario
    from app.schemas.scenario import (
        ScenarioCreateRequest,
        ScenarioSimulationSchema,
        ScenarioSummarySchema,
    )
    print("  scenario schemas importable  OK")

    # dashboard
    from app.schemas.dashboard import DashboardSchema
    print("  dashboard schema importable  OK")

    # evidence
    from app.schemas.evidence import EvidenceListSchema
    print("  evidence schema importable  OK")


# ── 3. Repositories importable ───────────────────────────────────────────────

def test_repositories() -> None:
    from app.repositories.supplier_repository import SupplierRepository
    from app.repositories.recommendation_repository import RecommendationRepository
    from app.repositories.scenario_repository import ScenarioRepository
    from app.repositories.evidence_repository import EvidenceRepository
    from app.repositories.project_repository import ProjectRepository
    print("  all Phase 4 repositories importable  OK")


# ── 4. Services importable ───────────────────────────────────────────────────

def test_services() -> None:
    from app.services.supplier_service import SupplierService
    from app.services.recommendation_service import RecommendationService
    from app.services.scenario_service import ScenarioService
    from app.services.dashboard_service import DashboardService
    from app.services.evidence_service import EvidenceService
    print("  all Phase 4 services importable  OK")


# ── 5. Standard envelope validation ─────────────────────────────────────────

def test_standard_envelope() -> None:
    from app.schemas.common import APIResponse

    # success envelope
    env = APIResponse(success=True, message="Suppliers retrieved.", data=[1, 2, 3], meta=None)
    dumped = env.model_dump()
    for field in ("success", "message", "data", "meta"):
        assert field in dumped, f"Envelope missing field: {field}"

    # error: success=False, data=None
    err = APIResponse(success=False, message="Not found.", data=None, meta=None)
    assert err.success is False
    assert err.data is None
    print("  standard envelope shape  OK")


# ── 6. Swagger/OpenAPI schema generates without errors ──────────────────────

def test_openapi_schema() -> None:
    from app.main import app
    schema = app.openapi()
    assert "paths" in schema, "OpenAPI schema has no paths"
    phase4_paths = [p for p in schema["paths"] if any(
        seg in p for seg in ["suppliers", "recommendations", "scenarios", "dashboard", "evidence"]
    )]
    assert len(phase4_paths) >= 5, f"Expected >=5 Phase 4 paths in OpenAPI, got {len(phase4_paths)}"
    print(f"  OpenAPI schema OK — {len(phase4_paths)} Phase 4 paths documented")


# ── Runner ───────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("\n=== Phase 4 Smoke Tests ===\n")
    tests = [
        ("routes_registered",  test_routes_registered),
        ("schemas",            test_schemas),
        ("repositories",       test_repositories),
        ("services",           test_services),
        ("standard_envelope",  test_standard_envelope),
        ("openapi_schema",     test_openapi_schema),
    ]
    failures = []
    for name, fn in tests:
        print(f"[{name}]")
        try:
            fn()
        except Exception as exc:
            print(f"  FAILED: {exc}")
            failures.append(name)
        print()

    if failures:
        print(f"FAILED tests: {failures}")
        sys.exit(1)
    else:
        print("All Phase 4 smoke tests passed.")
