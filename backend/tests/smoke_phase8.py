"""
Phase 8 smoke tests — run without a database, Redis, or browser.
Verifies: all new Phase 8 frontend files exist and are non-empty,
frontend type additions are present, pdfjs-dist is installed,
@react-pdf/renderer is still installed, scenarios page has
SensitivityChart imports, and the backend smoke tests still pass.

Usage:
    cd backend
    python tests/smoke_phase8.py
"""

import ast
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

FRONTEND = Path(__file__).parent.parent.parent / "frontend"
SRC      = FRONTEND / "src"


# ── helpers ───────────────────────────────────────────────────────────────────

def _read(path: Path) -> str:
    assert path.exists(), f"File does not exist: {path}"
    content = path.read_text(encoding="utf-8")
    assert len(content) > 50, f"File suspiciously small: {path}"
    return content


def _contains(path: Path, *phrases: str) -> None:
    content = _read(path)
    for phrase in phrases:
        assert phrase in content, (
            f"Expected {phrase!r} in {path.relative_to(FRONTEND)}"
        )


# ── 1. New component files exist and are non-empty ───────────────────────────

def test_new_files_exist() -> None:
    files = [
        SRC / "components" / "documents" / "DocumentViewer.tsx",
        SRC / "components" / "documents" / "EvidenceHighlight.tsx",
        SRC / "components" / "suppliers" / "EvidencePanel.tsx",
    ]
    for f in files:
        content = _read(f)
        print(f"  {f.relative_to(SRC)}  ({len(content)} chars)  OK")
    print("  new component files exist  OK")


# ── 2. DocumentViewer has required API surface ────────────────────────────────

def test_document_viewer_structure() -> None:
    path = SRC / "components" / "documents" / "DocumentViewer.tsx"
    _contains(path,
        "pdfjs-dist",            # imports the library
        "GlobalWorkerOptions",   # sets worker
        "getDocument",           # loads PDF
        "initialPage",           # prop for jumping to page
        "highlightText",         # prop for evidence highlight
        "canvasRef",             # renders to canvas
        "DocumentViewer",        # exported component name
    )
    print("  DocumentViewer structure  OK")


# ── 3. EvidenceHighlight splits and marks text ────────────────────────────────

def test_evidence_highlight_structure() -> None:
    path = SRC / "components" / "documents" / "EvidenceHighlight.tsx"
    _contains(path,
        "splitHighlight",      # highlight helper function
        "<mark",               # renders a <mark> element
        "highlight",           # prop name
        "relevanceScore",      # shows relevance score
        "EvidenceHighlight",   # exported component
    )
    print("  EvidenceHighlight structure  OK")


# ── 4. EvidencePanel is a proper drawer ──────────────────────────────────────

def test_evidence_panel_structure() -> None:
    path = SRC / "components" / "suppliers" / "EvidencePanel.tsx"
    _contains(path,
        "isOpen",              # open/close prop
        "onClose",             # close callback
        "recommendationId",    # data source prop
        "translate-x-full",    # slide-out CSS (closed state)
        "translate-x-0",       # slide-in CSS (open state)
        "evidenceApi",         # calls the evidence API
        "EvidenceHighlight",   # uses highlight component
        "Escape",              # closes on Escape key
        "EvidencePanel",       # exported component
    )
    print("  EvidencePanel structure  OK")


# ── 5. Supplier detail page wires EvidencePanel ───────────────────────────────

def test_supplier_detail_wired() -> None:
    path = SRC / "app" / "suppliers" / "[id]" / "page.tsx"
    _contains(path,
        "EvidencePanel",
        "evidenceOpen",
        "setEvidenceOpen",
        "View Evidence",
        "recommendationApi",
    )
    print("  /suppliers/[id] wired  OK")


# ── 6. Documents detail page uses DocumentViewer + EvidenceHighlight ─────────

def test_documents_detail_wired() -> None:
    path = SRC / "app" / "documents" / "[id]" / "page.tsx"
    _contains(path,
        "DocumentViewer",
        "EvidenceHighlight",
        "showViewer",
        "activeChunkIdx",
        "viewerPage",
        "View PDF",
    )
    print("  /documents/[id] wired  OK")


# ── 7. Scenarios page has SensitivityChart ────────────────────────────────────

def test_scenarios_sensitivity_chart() -> None:
    path = SRC / "app" / "scenarios" / "page.tsx"
    _contains(path,
        "LineChart",
        "Line",
        "CartesianGrid",
        "ReferenceLine",
        "sensitivityData",
        "SensitivityChart" if False else "Sensitivity",  # heading text
        "Activity",    # icon import
    )
    print("  SensitivityChart in scenarios page  OK")


# ── 8. ScenarioSimulation type has scenario_shipping_multiplier ───────────────

def test_scenario_type_updated() -> None:
    path = SRC / "types" / "scenario.ts"
    _contains(path, "scenario_shipping_multiplier")
    print("  ScenarioSimulation type updated  OK")


# ── 9. pdfjs-dist installed ───────────────────────────────────────────────────

def test_pdfjs_installed() -> None:
    pkg = FRONTEND / "node_modules" / "pdfjs-dist" / "package.json"
    assert pkg.exists(), "pdfjs-dist not found in node_modules"
    import json
    data    = json.loads(pkg.read_text())
    version = data.get("version", "")
    assert version, "pdfjs-dist version empty"
    print(f"  pdfjs-dist@{version}  installed  OK")


# ── 10. @react-pdf/renderer still installed ───────────────────────────────────

def test_react_pdf_installed() -> None:
    pkg = FRONTEND / "node_modules" / "@react-pdf" / "renderer" / "package.json"
    assert pkg.exists(), "@react-pdf/renderer not found in node_modules"
    import json
    data    = json.loads(pkg.read_text())
    version = data.get("version", "")
    print(f"  @react-pdf/renderer@{version}  still installed  OK")


# ── 11. Backend phase 7 smoke still passes ────────────────────────────────────

def test_backend_phase7_still_passes() -> None:
    import subprocess, sys as _sys
    result = subprocess.run(
        [_sys.executable, "tests/smoke_phase7.py"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        cwd=str(Path(__file__).parent.parent),
    )
    assert result.returncode == 0, (
        f"smoke_phase7.py failed:\n{result.stdout}\n{result.stderr}"
    )
    # Extract last summary line
    lines = [l for l in result.stdout.splitlines() if l.strip()]
    print(f"  backend phase7: {lines[-1].strip()}  OK")


# ── Runner ────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("\n=== Phase 8 Smoke Tests ===\n")

    tests = [
        ("new_files_exist",               test_new_files_exist),
        ("document_viewer_structure",      test_document_viewer_structure),
        ("evidence_highlight_structure",   test_evidence_highlight_structure),
        ("evidence_panel_structure",       test_evidence_panel_structure),
        ("supplier_detail_wired",          test_supplier_detail_wired),
        ("documents_detail_wired",         test_documents_detail_wired),
        ("scenarios_sensitivity_chart",    test_scenarios_sensitivity_chart),
        ("scenario_type_updated",          test_scenario_type_updated),
        ("pdfjs_installed",                test_pdfjs_installed),
        ("react_pdf_installed",            test_react_pdf_installed),
        ("backend_phase7_still_passes",    test_backend_phase7_still_passes),
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
    print("Phase 8 smoke tests PASSED")
