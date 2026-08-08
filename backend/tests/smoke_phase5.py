"""
Phase 5 smoke tests — run without a database or Redis.
Verifies all utility code works correctly in isolation.

Usage:
    cd backend
    python tests/smoke_phase5.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


def test_sanitizer() -> None:
    from app.utils.sanitizer import sanitize_filename, storage_filename

    cases = [
        # Path traversal: Path.stem of '../../../etc/passwd' is 'passwd' — traversal stripped
        ("../../../etc/passwd",  "passwd"),
        ("normal_file.docx",     "normal_file.docx"),
        ("My Invoice (2026).PDF", None),          # must not crash; check extension
        ("  ..hidden..  ",       None),            # must not crash
        ("",                     None),            # fallback to uuid.bin
    ]
    for inp, expected_contains in cases:
        result = sanitize_filename(inp)
        assert isinstance(result, str) and len(result) > 0, f"Empty result for {inp!r}"
        if expected_contains:
            assert expected_contains in result, f"Expected {expected_contains!r} in {result!r}"
        print(f"  sanitize_filename({inp!r:35}) -> {result!r}")

    sfn = storage_filename("../../secret.pdf")
    assert sfn.endswith(".pdf"), f"Expected .pdf extension, got {sfn}"
    assert len(sfn) > 10, "UUID too short"
    print(f"  storage_filename -> {sfn}")

    print("  sanitizer OK")


def test_file_validator() -> None:
    from app.utils.file_validator import validate_upload

    pdf_path = Path(__file__).parent.parent.parent / "sample-data" / "documents" / "Acme_Precision_Quotation_Q4_2026.pdf"
    pdf_bytes = pdf_path.read_bytes()

    # Valid PDF
    r = validate_upload(pdf_bytes, "Acme_Precision_Quotation_Q4_2026.pdf")
    assert r.valid is True, f"Expected valid, got: {r.error_message}"
    assert r.file_type == "pdf"
    assert r.file_size_bytes == len(pdf_bytes)
    assert len(r.sha256_checksum) == 64
    print(f"  valid PDF   -> valid={r.valid} type={r.file_type} size={r.file_size_bytes}B")

    # Fake content
    r2 = validate_upload(b"not a real file", "fake.pdf")
    assert r2.valid is False
    assert r2.error_code == "INVALID_FILE_CONTENT"
    print(f"  fake file   -> valid={r2.valid} code={r2.error_code}")

    # Empty
    r3 = validate_upload(b"", "empty.pdf")
    assert r3.valid is False
    assert r3.error_code == "FILE_EMPTY"
    print(f"  empty file  -> valid={r3.valid} code={r3.error_code}")

    # Bad extension
    r4 = validate_upload(pdf_bytes, "file.exe")
    assert r4.valid is False
    assert r4.error_code == "INVALID_FILE_TYPE"
    print(f"  bad ext     -> valid={r4.valid} code={r4.error_code}")

    print("  file_validator OK")


def test_chunker() -> None:
    from app.utils.chunker import chunk_pages, chunk_text

    pages = [
        (1, (
            "COMMERCIAL QUOTATION\n"
            "Acme Precision Manufacturing. Unit Price: USD 95.00 per unit. "
            "Shipping: USD 22.00. Lead Time: 14 days. ISO 9001:2015 certified. "
            "AS9100D certified. Defect rate below 0.1 percent. "
            "On-time delivery record 97 percent over the last 24 months."
        )),
        (2, (
            "DELIVERY TERMS\n"
            "FOB Stuttgart. International freight via DHL Express. "
            "Production capacity currently at 95 percent. "
            "Certificate of Conformance included with each shipment. "
            "First Article Inspection available upon request."
        )),
    ]
    chunks = chunk_pages(pages)
    assert len(chunks) >= 1, "Expected at least one chunk"
    for c in chunks:
        assert c.content, "Empty chunk content"
        assert c.page_number >= 1
        assert c.token_count > 0
        assert c.chunk_index >= 0
        print(f"  chunk[{c.chunk_index}] page={c.page_number} tokens={c.token_count} "
              f"section={c.section_name!r} | {c.content[:55]!r}...")

    # Single-text convenience wrapper
    single = chunk_text("Short text for testing.", page_number=3)
    assert len(single) == 1
    assert single[0].page_number == 3

    # Determinism
    chunks_a = chunk_pages(pages)
    chunks_b = chunk_pages(pages)
    assert [c.content for c in chunks_a] == [c.content for c in chunks_b], "Chunker is not deterministic"

    print("  chunker OK")


def test_schemas_import() -> None:
    from app.schemas.document import (
        DocumentChunkSchema,
        DocumentListSchema,
        DocumentStatusResponse,
        DocumentSummarySchema,
        DocumentUploadResponse,
        JobStatusResponse,
    )
    # Instantiate each to confirm field definitions are valid
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)

    u = DocumentUploadResponse(
        document_id="abc", filename="test.pdf", file_type="pdf",
        file_size_bytes=1024, status="uploaded", job_id="task-1"
    )
    assert u.document_id == "abc"

    s = DocumentStatusResponse(
        document_id="abc", filename="test.pdf", status="uploaded",
        progress=5, chunk_count=0, created_at=now, updated_at=now
    )
    assert s.progress == 5

    j = JobStatusResponse(job_id="task-1", document_id="abc", status="processing", progress=20)
    assert j.status == "processing"

    print("  schemas OK")


def test_routes_registered() -> None:
    from app.main import app
    paths = {r.path for r in app.routes if hasattr(r, "path")}
    expected = {
        "/api/v1/documents/upload",
        "/api/v1/documents",
        "/api/v1/documents/{document_id}",
        "/api/v1/documents/{document_id}/chunks",
        "/api/v1/jobs/{job_id}",
    }
    missing = expected - paths
    assert not missing, f"Missing routes: {missing}"
    print(f"  All {len(expected)} document routes registered OK")


if __name__ == "__main__":
    print("\n=== Phase 5 Smoke Tests ===\n")
    failures = []
    for name, fn in [
        ("sanitizer",         test_sanitizer),
        ("file_validator",    test_file_validator),
        ("chunker",           test_chunker),
        ("schemas",           test_schemas_import),
        ("routes_registered", test_routes_registered),
    ]:
        print(f"[{name}]")
        try:
            fn()
        except Exception as exc:
            print(f"  FAILED: {exc}")
            failures.append(name)
        print()

    if failures:
        print(f"FAILED: {failures}")
        sys.exit(1)
    else:
        print("All Phase 5 smoke tests passed.")
