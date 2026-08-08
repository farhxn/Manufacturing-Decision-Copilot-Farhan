"""
Direct document processor — runs extract → chunk → embed → index
without requiring Celery or Redis. Safe to run multiple times (idempotent).

Usage:
    cd backend
    python ../scripts/process_documents_direct.py
"""
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

import psycopg2
from app.core.config import settings
from app.core.logging import get_logger
from app.workers.document_worker import (
    _extract_text,
    _save_chunks,
    _upsert_to_chroma,
)
from app.utils.chunker import chunk_pages
from app.ai.embeddings import embed_texts

logger = get_logger(__name__)

BATCH_SIZE = 50  # embeddings per API call


def get_sync_conn():
    return psycopg2.connect(settings.database_url.replace("+asyncpg", ""))


def get_unchunked_documents():
    """Return all documents that have 0 chunks."""
    conn = get_sync_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT d.id, d.file_path, d.file_type,
                       d.project_id::text, d.supplier_id::text, d.filename
                FROM documents d
                LEFT JOIN document_chunks dc ON dc.document_id = d.id
                GROUP BY d.id, d.file_path, d.file_type,
                         d.project_id, d.supplier_id, d.filename
                HAVING COUNT(dc.id) = 0
                ORDER BY d.filename
            """)
            return cur.fetchall()
    finally:
        conn.close()


def set_status(doc_id: str, status: str):
    conn = get_sync_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE documents SET status = %s, updated_at = NOW() WHERE id = %s",
                (status, doc_id),
            )
        conn.commit()
    finally:
        conn.close()


def process_document(doc_id, file_path, file_type, project_id, supplier_id, filename):
    print(f"\n  Processing: {filename}")
    print(f"    file_path : {file_path}")

    # 1. Check file exists on disk
    if not Path(file_path).exists():
        print(f"    [SKIP] File not on disk: {file_path}")
        return False

    set_status(doc_id, "processing")

    # 2. Extract text
    try:
        pages = _extract_text(file_path, file_type)
    except Exception as e:
        print(f"    [ERROR] Extract failed: {e}")
        set_status(doc_id, "error")
        return False

    if not pages:
        print(f"    [ERROR] No text extracted")
        set_status(doc_id, "error")
        return False

    total_chars = sum(len(t) for _, t in pages)
    print(f"    extracted  : {len(pages)} page(s), {total_chars} chars")

    # 3. Chunk
    chunks = chunk_pages(pages)
    if not chunks:
        print(f"    [ERROR] Chunker produced 0 chunks")
        set_status(doc_id, "error")
        return False

    print(f"    chunks     : {len(chunks)}")

    # 4. Embed
    set_status(doc_id, "indexing")
    texts = [c.content for c in chunks]
    all_embeddings = []
    for i in range(0, len(texts), BATCH_SIZE):
        batch = texts[i: i + BATCH_SIZE]
        try:
            all_embeddings.extend(embed_texts(batch))
        except Exception as e:
            print(f"    [ERROR] Embedding batch {i} failed: {e}")
            set_status(doc_id, "error")
            return False

    print(f"    embeddings : {len(all_embeddings)} vectors")

    # 5. Upsert into ChromaDB
    try:
        _upsert_to_chroma(doc_id, project_id, supplier_id, chunks, all_embeddings)
    except Exception as e:
        print(f"    [WARN] ChromaDB upsert failed (non-fatal): {e}")

    # 6. Save chunks to Postgres
    _save_chunks(doc_id, chunks)

    # 7. Mark completed
    set_status(doc_id, "completed")
    print(f"    [DONE] {len(chunks)} chunks saved")
    return True


def main():
    print("\n=== Direct Document Processor ===\n")
    docs = get_unchunked_documents()
    print(f"Found {len(docs)} document(s) with 0 chunks\n")

    if not docs:
        print("Nothing to process — all documents already have chunks.")
        return

    success = 0
    failed = 0
    for row in docs:
        doc_id, file_path, file_type, project_id, supplier_id, filename = row
        ok = process_document(
            doc_id, file_path, file_type, project_id, supplier_id, filename
        )
        if ok:
            success += 1
        else:
            failed += 1

    # Final summary
    print(f"\n{'='*50}")
    print(f"  Processed : {success}/{len(docs)}")
    if failed:
        print(f"  Failed    : {failed}")

    # Verify chunk counts
    conn = get_sync_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT d.filename, COUNT(dc.id) as chunk_count
                FROM documents d
                LEFT JOIN document_chunks dc ON dc.document_id = d.id
                GROUP BY d.id, d.filename
                ORDER BY d.filename
            """)
            rows = cur.fetchall()
    finally:
        conn.close()

    print(f"\n{'Filename':<52} {'Chunks':>7}")
    print("-" * 60)
    total_chunks = 0
    for filename, cnt in rows:
        status = "OK" if cnt > 0 else "EMPTY"
        print(f"  [{status:<5}] {filename:<48} {cnt:>5}")
        total_chunks += cnt

    print(f"\n  Total chunks in DB: {total_chunks}")
    print(f"{'='*50}\n")


if __name__ == "__main__":
    main()
