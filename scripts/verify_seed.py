"""
Quick verification script — runs live scoring against the seeded DB
and asserts all edge-case behaviours are correct.

Usage:
    cd backend
    python ../scripts/verify_seed.py
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from sqlalchemy import text

from app.database.session import AsyncSessionLocal
from app.engines.ranking import score_suppliers
from app.repositories.project_repository import ProjectRepository
from app.repositories.supplier_repository import SupplierRepository
from app.services.supplier_mapper import (
    DEFAULT_REQUIRED_CERTS,
    project_to_weights,
    suppliers_to_inputs,
)

PROJECT_ID = "00000000-0000-4000-a000-000000000002"

TABLES = [
    "organizations", "projects", "users", "suppliers",
    "supplier_certifications", "supplier_risk_scores",
    "supplier_prices", "documents", "scenarios",
]


async def verify() -> None:
    async with AsyncSessionLocal() as session:
        sup_repo  = SupplierRepository(session)
        proj_repo = ProjectRepository(session)

        # ── Row counts ────────────────────────────────────────────────────
        print("\n=== DB ROW COUNTS ===")
        for t in TABLES:
            r = await session.execute(text(f"SELECT COUNT(*) FROM {t}"))  # noqa: S608
            print(f"  {t:<35} {r.scalar()}")

        # ── Load and score ────────────────────────────────────────────────
        suppliers = await sup_repo.list_by_project(PROJECT_ID, limit=50, offset=0)
        project   = await proj_repo.get_by_id(PROJECT_ID)
        weights   = project_to_weights(project)
        inputs    = suppliers_to_inputs(suppliers)

        ranking = score_suppliers(
            suppliers=inputs,
            weights=weights,
            required_certs=list(DEFAULT_REQUIRED_CERTS),
        )

        name_map = {s.id: s.name for s in suppliers}

        print("\n=== LIVE SCORING — BASELINE (default weights) ===")
        header = (
            f"  {'Rank':<5} {'Supplier':<28} {'Country':<14}"
            f" {'LandedUSD':<11} {'Score':<8} {'Compliance':<12}"
            f" {'Risk':<8} Notes"
        )
        print(header)
        print("  " + "-" * 100)

        for r in ranking:
            s_obj   = next(s for s in suppliers if s.id == r.supplier_id)
            name    = s_obj.name[:27]
            country = s_obj.country[:13]
            comp    = "PASS" if r.compliance_score == 100 else f"FAIL({r.compliance_score:.0f})"
            notes   = ""
            if r.compliance_score == 0:
                notes = "<-- COMPLIANCE ZERO"
            elif r.cost_score < 50:
                notes = "<-- LOW COST SCORE"
            elif s_obj.risk_level == "High":
                notes = "<-- HIGH RISK"
            print(
                f"  #{r.rank:<4} {name:<28} {country:<14}"
                f" {r.landed_cost:<11.2f} {r.final_score:<8.2f} {comp:<12}"
                f" {r.risk_score:<8.2f} {notes}"
            )

        # ── Edge case assertions ──────────────────────────────────────────
        print("\n=== EDGE CASE ASSERTIONS ===")
        by_name = {name_map[r.supplier_id]: r for r in ranking}
        failures = []

        def check(label: str, cond: bool, detail: str = "") -> None:
            if cond:
                print(f"  [PASS] {label}")
            else:
                print(f"  [FAIL] {label}  {detail}")
                failures.append(label)

        # 1. Acme ranks #1 at baseline
        acme = by_name.get("Acme Precision Mfg")
        check(
            "Acme Precision Mfg ranked #1 (baseline)",
            acme is not None and acme.rank == 1,
            f"actual rank={acme.rank if acme else 'missing'}",
        )

        # 2. PeakMetal compliance = 0 (expired cert, is_valid=False)
        peak = by_name.get("PeakMetal Solutions")
        check(
            "PeakMetal Solutions compliance_score = 0 (expired ISO cert, is_valid=False)",
            peak is not None and peak.compliance_score == 0.0,
            f"actual={peak.compliance_score if peak else 'missing'}",
        )

        # 3. AlphaForge compliance = 0 (no certs at all)
        alpha = by_name.get("AlphaForge Ltd")
        check(
            "AlphaForge Ltd compliance_score = 0 (no certifications held)",
            alpha is not None and alpha.compliance_score == 0.0,
            f"actual={alpha.compliance_score if alpha else 'missing'}",
        )

        # 4. SteelPath risk_score < 60 (BB- credit + high country risk)
        steel = by_name.get("SteelPath Industries")
        check(
            f"SteelPath Industries risk_score < 60 (got {steel.risk_score:.2f})",
            steel is not None and steel.risk_score < 60.0,
            f"actual={steel.risk_score if steel else 'missing'}",
        )

        # 5. FastTrack has the lowest landed cost among the 7 "standard" suppliers
        #    (excludes SteelPath/PeakMetal/AlphaForge edge cases by name)
        EDGE_NAMES = {"SteelPath Industries", "PeakMetal Solutions", "AlphaForge Ltd"}
        standard   = [r for r in ranking if name_map[r.supplier_id] not in EDGE_NAMES]
        cheapest   = min(standard, key=lambda r: r.landed_cost)
        check(
            f"FastTrack Manufacturing lowest landed cost among 7 standard suppliers ({cheapest.landed_cost:.2f} USD)",
            name_map[cheapest.supplier_id] == "FastTrack Manufacturing",
            f"actual cheapest={name_map[cheapest.supplier_id]} @ {cheapest.landed_cost:.2f}",
        )

        # 6. GlobalFab has highest absolute landed cost (25% duty penalty)
        globalfab   = by_name.get("Global Fabrication Ltd")
        max_landed  = max(r.landed_cost for r in ranking)
        check(
            f"Global Fabrication Ltd has highest landed cost ({globalfab.landed_cost:.2f} USD)",
            globalfab is not None and globalfab.landed_cost == max_landed,
            f"actual max={max_landed:.2f}",
        )

        # 7. Exactly 2 suppliers have compliance_score = 0
        zero_comp = [r for r in ranking if r.compliance_score == 0.0]
        check(
            f"Exactly 2 suppliers with compliance_score=0 (PeakMetal + AlphaForge)",
            len(zero_comp) == 2,
            f"actual count={len(zero_comp)}",
        )

        # 8. NovaCast and Acme both have AS9100D (aerospace cert present)
        for s in suppliers:
            if s.name in ("Acme Precision Mfg", "NovaCast Engineering"):
                has_as = any("AS9100D" in c.name for c in s.certifications if c.is_valid)
                check(f"{s.name} holds valid AS9100D", has_as)

        # ── Summary ───────────────────────────────────────────────────────
        print()
        if not failures:
            print("  *** ALL ASSERTIONS PASSED — database is production-ready ***")
        else:
            print(f"  *** {len(failures)} ASSERTION(S) FAILED: {failures} ***")
            sys.exit(1)


if __name__ == "__main__":
    asyncio.run(verify())
