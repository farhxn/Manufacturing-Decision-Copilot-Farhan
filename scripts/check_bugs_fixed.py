"""
Verifies both PDF bugs are fixed:
  Bug 1 — PDF text layer not extractable (Td vs Tm operator)
  Bug 2 — Documents producing 0 or 1 chunks (too short for chunker)

Also checks sentence-transformers install status and embeddings mode.

Usage:
    cd backend
    python ../scripts/check_bugs_fixed.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

import fitz
import psycopg2
from app.core.config import settings
from app.utils.chunker import chunk_pages, TARGET_CHARS

DOCS_DIR = Path(__file__).parent.parent / "sample-data" / "documents"
MIN_LINES_PER_PDF = 10       # extractable text threshold
MIN_CHUNKS_PER_DOC = 2       # chunking threshold


def check_bug1_text_extraction():
    """Bug 1: Verify every PDF has a proper text layer (>= MIN_LINES lines)."""
    print("\n=== BUG 1: PDF text extraction (Tm vs Td fix) ===\n")
    pdfs = sorted(DOCS_DIR.glob("*.pdf"))
    if not pdfs:
        print("  ERROR: No PDFs found in", DOCS_DIR)
        return False

    results = []
    for pdf_path in pdfs:
        doc = fitz.open(str(pdf_path))
        all_text = ""
        num_pages = doc.page_count
        for page in doc:
            all_text += page.get_text("text")
        doc.close()
        lines = [l.strip() for l in all_text.splitlines() if l.strip()]
        ok = len(lines) >= MIN_LINES_PER_PDF
        results.append((pdf_path.name, num_pages, len(lines), ok))
        status = "PASS" if ok else "FAIL"
        print(f"  [{status}] {pdf_path.name:<52} pages={num_pages}  lines={len(lines):>3}")

    failed = [r for r in results if not r[3]]
    print()
    if failed:
        print(f"  Bug 1 STATUS: STILL BROKEN — {len(failed)} PDF(s) have < {MIN_LINES_PER_PDF} extractable lines:")
        for r in failed:
            print(f"    {r[0]}  (lines={r[2]})")
        return False
    else:
        print(f"  Bug 1 STATUS: FIXED — all {len(results)} PDFs have full text layer")
        return True


def check_bug2_chunking():
    """Bug 2: Verify DB documents have >= MIN_CHUNKS_PER_DOC chunks each."""
    print("\n=== BUG 2: Document chunking (content length fix) ===\n")
    conn = psycopg2.connect(settings.database_url.replace("+asyncpg", ""))
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT d.filename, COUNT(dc.id) as chunks, d.status
                FROM documents d
                LEFT JOIN document_chunks dc ON dc.document_id = d.id
                GROUP BY d.id, d.filename, d.status
                ORDER BY d.filename
            """)
            rows = cur.fetchall()
    finally:
        conn.close()

    if not rows:
        print("  ERROR: No document records in database.")
        return False

    total_chunks = 0
    failed = []
    for filename, chunk_count, status in rows:
        total_chunks += chunk_count
        ok = chunk_count >= MIN_CHUNKS_PER_DOC
        if not ok:
            failed.append((filename, chunk_count, status))
        label = "PASS" if ok else "FAIL"
        print(f"  [{label}] {filename:<52} chunks={chunk_count:>3}  status={status}")

    print()
    print(f"  Total documents : {len(rows)}")
    print(f"  Total chunks    : {total_chunks}")
    print(f"  Avg chunks/doc  : {total_chunks/len(rows):.1f}")

    if failed:
        print(f"\n  Bug 2 STATUS: STILL BROKEN — {len(failed)} document(s) have < {MIN_CHUNKS_PER_DOC} chunks:")
        for f in failed:
            print(f"    {f[0]}  (chunks={f[1]}, status={f[2]})")
        return False
    else:
        print(f"\n  Bug 2 STATUS: FIXED — all {len(rows)} documents have >= {MIN_CHUNKS_PER_DOC} chunks")
        return True


def check_chunker_on_live_pdf():
    """Demonstrate the chunker actually splits a PDF into multiple chunks."""
    print("\n=== CHUNKER LIVE TEST: Acme quotation (largest PDF) ===\n")
    pdf_path = DOCS_DIR / "Acme_Precision_Quotation_Q4_2026.pdf"
    if not pdf_path.exists():
        print("  SKIP: PDF not found")
        return

    doc = fitz.open(str(pdf_path))
    pages = []
    for i, page in enumerate(doc):
        text = page.get_text("text").strip()
        if text:
            pages.append((i + 1, text))
    doc.close()

    total_chars = sum(len(t) for _, t in pages)
    chunks = chunk_pages(pages)

    print(f"  Chunker target  : {TARGET_CHARS} chars")
    print(f"  PDF pages       : {len(pages)}")
    print(f"  Total chars     : {total_chars}")
    print(f"  Chunks produced : {len(chunks)}")
    print()
    for c in chunks:
        preview = c.content[:80].replace("\n", " ")
        print(f"  chunk[{c.chunk_index}] page={c.page_number} tokens={c.token_count:>4}  section={c.section_name!r}")
        print(f"    {preview}...")


def check_embeddings_mode():
    """Warn if sentence-transformers is not installed (zero-vector mode)."""
    print("\n=== EMBEDDING MODE CHECK ===\n")
    try:
        import sentence_transformers
        print(f"  sentence-transformers : INSTALLED (v{sentence_transformers.__version__})")
        print("  Embedding mode        : REAL semantic vectors")
        print("  RAG retrieval         : FULLY FUNCTIONAL")
    except ImportError:
        print("  sentence-transformers : NOT INSTALLED")
        print("  Embedding mode        : ZERO VECTORS (demo/CI mode)")
        print("  RAG retrieval         : Non-functional — queries return random results")
        print()
        print("  To fix, run in the backend venv:")
        print("    pip install sentence-transformers")
        print("  (uses BAAI/bge-small-en-v1.5 as per config local_embedding_model)")


def main():
    print("=" * 65)
    print("  PDF PIPELINE BUG VERIFICATION")
    print("=" * 65)

    b1 = check_bug1_text_extraction()
    b2 = check_bug2_chunking()
    check_chunker_on_live_pdf()
    check_embeddings_mode()

    print("\n" + "=" * 65)
    print("  SUMMARY")
    print("=" * 65)
    print(f"  Bug 1 (Td/Tm — text extraction) : {'FIXED' if b1 else 'BROKEN'}")
    print(f"  Bug 2 (chunk count = 0/1)        : {'FIXED' if b2 else 'BROKEN'}")
    if b1 and b2:
        print("\n  Both bugs are fixed. Documents are properly chunked and indexed.")
    else:
        print("\n  One or more bugs remain. See details above.")
    print("=" * 65 + "\n")

    sys.exit(0 if (b1 and b2) else 1)


if __name__ == "__main__":
    main()
