"""
Phase 9 smoke tests — verifies polish layer: Framer Motion wiring,
loading/error boundaries, ARIA attributes, report history, and that
all prior smoke tests still pass.

Usage:
    cd backend
    python tests/smoke_phase9.py
"""

import subprocess
import sys
from pathlib import Path

SRC = Path(__file__).parent.parent.parent / "frontend" / "src"


def _read(path: Path) -> str:
    assert path.exists(), f"Missing: {path.relative_to(SRC.parent.parent)}"
    content = path.read_text(encoding="utf-8")
    assert len(content) > 20, f"File too small: {path.name}"
    return content


def _contains(path: Path, *phrases: str) -> None:
    content = _read(path)
    for phrase in phrases:
        assert phrase in content, (
            f"Expected {phrase!r} in {path.relative_to(SRC)}"
        )


# ── 1. PageTransition component exists and is correct ────────────────────────

def test_page_transition_component() -> None:
    path = SRC / "components" / "layout" / "PageTransition.tsx"
    _contains(path,
        "AnimatePresence",
        "motion.div",
        "routeKey",
        "mode=\"wait\"",
        "PageTransition",
    )
    print("  PageTransition component  OK")


# ── 2. AppLayout wires PageTransition ────────────────────────────────────────

def test_applayout_wired() -> None:
    path = SRC / "components" / "layout" / "AppLayout.tsx"
    _contains(path,
        "PageTransition",
        "usePathname",
        "routeKey",
    )
    print("  AppLayout wired  OK")


# ── 3. Dashboard KPI strip uses motion.div ───────────────────────────────────

def test_dashboard_motion() -> None:
    path = SRC / "app" / "dashboard" / "page.tsx"
    _contains(path, "motion.div", "framer-motion")
    print("  Dashboard Framer Motion  OK")


# ── 4. Reports page has history, AnimatePresence, reportApi ──────────────────

def test_reports_history() -> None:
    path = SRC / "app" / "reports" / "page.tsx"
    _contains(path,
        "reportApi",
        "AnimatePresence",
        "historyReports",
        "Report History",
        "deleteReportMutation",
        "aria-label",
    )
    print("  Reports history + animations  OK")


# ── 5. Sidebar has aria-label and aria-current ───────────────────────────────

def test_sidebar_accessibility() -> None:
    path = SRC / "components" / "layout" / "Sidebar.tsx"
    _contains(path, "aria-label", "aria-current")
    print("  Sidebar ARIA attributes  OK")


# ── 6. loading.tsx files exist for all major routes ──────────────────────────

def test_loading_files() -> None:
    routes = ["dashboard", "suppliers", "documents", "scenarios", "reports"]
    for route in routes:
        f = SRC / "app" / route / "loading.tsx"
        assert f.exists(), f"Missing loading.tsx for /{route}"
    print(f"  loading.tsx present for {len(routes)} routes  OK")


# ── 7. error.tsx files exist for all major routes ────────────────────────────

def test_error_files() -> None:
    routes = ["dashboard", "suppliers", "documents", "scenarios", "reports"]
    for route in routes:
        f = SRC / "app" / route / "error.tsx"
        content = _read(f)
        assert "'use client'" in content, f"error.tsx for /{route} missing 'use client'"
        assert "reset" in content, f"error.tsx for /{route} missing reset prop"
    print(f"  error.tsx present (with reset) for {len(routes)} routes  OK")


# ── 8. framer-motion installed ───────────────────────────────────────────────

def test_framer_motion_installed() -> None:
    import json
    pkg = SRC.parent.parent / "node_modules" / "framer-motion" / "package.json"
    assert pkg.exists(), "framer-motion not in node_modules"
    version = json.loads(pkg.read_text())["version"]
    print(f"  framer-motion@{version}  OK")


# ── 9. Phase 8 smoke still passes ────────────────────────────────────────────

def test_phase8_still_passes() -> None:
    result = subprocess.run(
        [sys.executable, "tests/smoke_phase8.py"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        cwd=str(Path(__file__).parent.parent),
    )
    assert result.returncode == 0, (
        f"smoke_phase8.py failed:\n{result.stdout[-600:]}\n{result.stderr[-200:]}"
    )
    lines = [l for l in result.stdout.splitlines() if l.strip()]
    print(f"  phase8: {lines[-1].strip()}  OK")


# ── Runner ────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("\n=== Phase 9 Smoke Tests ===\n")

    tests = [
        ("page_transition_component",  test_page_transition_component),
        ("applayout_wired",            test_applayout_wired),
        ("dashboard_motion",           test_dashboard_motion),
        ("reports_history",            test_reports_history),
        ("sidebar_accessibility",      test_sidebar_accessibility),
        ("loading_files",              test_loading_files),
        ("error_files",                test_error_files),
        ("framer_motion_installed",    test_framer_motion_installed),
        ("phase8_still_passes",        test_phase8_still_passes),
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
    print("Phase 9 smoke tests PASSED")
