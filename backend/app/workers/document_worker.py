"""
Document processing Celery task.

Pipeline:
  uploaded → processing → extracting → indexing → completed
                                               ↘ error (any stage)

Each status update is committed to PostgreSQL immediately so the
frontend polling endpoint reflects real-time progress.

IMPORTANT — sync DB in Celery:
  Celery workers are synchronous processes.  The async SQLAlchemy engine
  (AsyncSessionLocal) is bound to the event loop that FastAPI creates at
  startup — that loop never exists inside a Celery worker process.
  Attempting to reuse it via asyncio.run() or asyncio.new_event_loop()
  raises "Future attached to a different loop".

  Solution: use a plain synchronous psycopg2 connection for all DB writes
  inside the worker.  The async engine is left exclusively for FastAPI.
"""

from __future__ import annotations

import uuid
from pathlib import Path
from typing import Any
import asyncio

from app.core.logging import get_logger
from app.workers.celery_app import celery_app

logger = get_logger(__name__)

# ── Status constants ──────────────────────────────────────────────────────────
S_PROCESSING  = "processing"
S_EXTRACTING  = "extracting"
S_INDEXING    = "indexing"
S_COMPLETED   = "completed"
S_ERROR       = "error"


# ── Synchronous DB helpers (psycopg2 — safe inside Celery) ───────────────────

def _get_sync_conn():
    """
    Open a fresh synchronous psycopg2 connection.

    Derives connection parameters from the async DATABASE_URL by stripping
    the +asyncpg driver suffix.  Each call opens and returns a new
    connection; callers are responsible for closing it.
    """
    import psycopg2
    from app.core.config import settings

    sync_url = settings.sync_database_url
    return psycopg2.connect(sync_url)


def _set_status(document_id: str, status: str) -> None:
    """Persist document status to PostgreSQL synchronously."""
    conn = _get_sync_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE documents SET status = %s, updated_at = NOW() WHERE id = %s",
                (status, document_id),
            )
        conn.commit()
    finally:
        conn.close()


def _load_document(document_id: str) -> dict | None:
    """
    Load the minimal document fields needed by the pipeline.
    Returns a plain dict or None if not found.
    """
    conn = _get_sync_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, file_path, file_type,
                       project_id::text, supplier_id::text
                FROM documents
                WHERE id = %s
                """,
                (document_id,),
            )
            row = cur.fetchone()
        if not row:
            return None
        return {
            "id":          row[0],
            "file_path":   row[1],
            "file_type":   row[2],
            "project_id":  row[3],
            "supplier_id": row[4],
        }
    finally:
        conn.close()


def _save_chunks(document_id: str, chunks: list[Any]) -> None:
    """Bulk-insert TextChunk objects as document_chunks rows."""
    if not chunks:
        return

    conn = _get_sync_conn()
    try:
        with conn.cursor() as cur:
            rows = [
                (
                    str(uuid.uuid4()),
                    document_id,
                    chunk.chunk_index,
                    chunk.page_number,
                    chunk.section_name,
                    chunk.content,
                    chunk.token_count,
                    1.0,   # extraction_confidence
                )
                for chunk in chunks
            ]
            cur.executemany(
                """
                INSERT INTO document_chunks
                    (id, document_id, chunk_index, page_number, section_name,
                     content, token_count, extraction_confidence)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                rows,
            )
        conn.commit()
    finally:
        conn.close()


def _invalidate_caches(project_id: str) -> None:
    """
    Invalidate Redis cache keys that become stale after a document is
    processed.  Uses fire-and-forget semantics — a Redis failure does NOT
    abort the pipeline.

    Keys invalidated (per Redis key conventions in the roadmap):
      recommendation:{project_id}
      dashboard:{project_id}
      supplier_scores:{project_id}
    """
    try:
        import redis
        from app.core.config import settings

        client = redis.from_url(settings.redis_url, decode_responses=True)
        keys = [
            f"recommendation:{project_id}",
            f"dashboard:{project_id}",
            f"supplier_scores:{project_id}",
        ]
        deleted = client.delete(*keys)
        client.close()
        logger.info(
            "Redis caches invalidated",
            project_id=project_id,
            keys_deleted=deleted,
        )
    except Exception as exc:          # noqa: BLE001
        logger.warning(
            "Redis cache invalidation failed (non-fatal)",
            project_id=project_id,
            error=str(exc),
        )


def _extract_and_update_supplier_sync(supplier_id: str, text: str) -> None:
    """Run extraction agent and update supplier profile synchronously."""
    from app.ai.client import build_agent, run_agent
    from app.ai.schemas import SupplierExtraction
    from app.ai.prompts.v1.extraction import SYSTEM_PROMPT, build_user_prompt

    logger.info("Running extraction agent", supplier_id=supplier_id)
    
    agent = build_agent(
        output_schema=SupplierExtraction,
        system_prompt=SYSTEM_PROMPT,
        retries=2,
    )
    user_prompt = build_user_prompt(text)
    
    # Run agent in isolated event loop since Celery worker is synchronous
    try:
        result: SupplierExtraction = asyncio.run(run_agent(agent, user_prompt))
        logger.info("Model response", result=result.model_dump())
    except Exception as exc:
        logger.warning(
            "Supplier extraction failed",
            supplier_id=supplier_id,
            error=str(exc),
        )
        return
        
    _update_supplier_sync(supplier_id, result)


def _update_supplier_sync(supplier_id: str, extraction) -> None:
    """Update supplier profile using psycopg2 synchronously."""
    conn = _get_sync_conn()
    try:
        with conn.cursor() as cur:
            # 1. Update basic fields if provided
            updates = {}
            if extraction.quoted_price is not None:
                updates["unit_price"] = extraction.quoted_price
            if extraction.currency is not None:
                updates["currency"] = extraction.currency
            if extraction.lead_time_days is not None:
                updates["lead_time_days"] = extraction.lead_time_days
                
            if updates:
                set_clause = ", ".join(f"{k} = %s" for k in updates.keys())
                values = list(updates.values())
                values.append(supplier_id)
                cur.execute(
                    f"UPDATE suppliers SET {set_clause}, updated_at = NOW() WHERE id = %s",
                    tuple(values),
                )
            
            # 2. Insert certifications
            if extraction.certifications:
                cert_rows = [
                    (str(uuid.uuid4()), supplier_id, cert_name, True)
                    for cert_name in extraction.certifications
                ]
                cur.executemany(
                    """
                    INSERT INTO supplier_certifications (id, supplier_id, name, is_valid)
                    VALUES (%s, %s, %s, %s)
                    """,
                    cert_rows,
                )
                
            # 3. Insert capabilities
            if extraction.capabilities:
                cap_rows = [
                    (str(uuid.uuid4()), supplier_id, cap_name, "General", True)
                    for cap_name in extraction.capabilities
                ]
                cur.executemany(
                    """
                    INSERT INTO supplier_capabilities (id, supplier_id, name, category, verified)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    cap_rows,
                )
                
        conn.commit()
        logger.info(
            "Supplier profile updated from extraction",
            supplier_id=supplier_id,
            certifications=len(extraction.certifications),
            capabilities=len(extraction.capabilities),
        )
    except Exception as exc:
        conn.rollback()
        logger.warning(
            "Failed to update supplier profile",
            supplier_id=supplier_id,
            error=str(exc),
        )
    finally:
        conn.close()


# ── Text extraction ───────────────────────────────────────────────────────────

def _extract_pdf(file_path: str) -> list[tuple[int, str]]:
    """
    Extract text from a PDF using PyMuPDF (fitz).
    Returns list of (1-indexed page number, page text).
    Falls back to pytesseract OCR for pages with no text layer.
    """
    try:
        import fitz  # PyMuPDF
    except ImportError as exc:
        raise RuntimeError("PyMuPDF (fitz) is not installed.") from exc

    pages: list[tuple[int, str]] = []
    doc = fitz.open(file_path)

    for page_num, page in enumerate(doc, start=1):
        text = page.get_text("text").strip()
        if text:
            pages.append((page_num, text))
        else:
            # No text layer — attempt OCR fallback
            ocr_text = _ocr_pdf_page(page, page_num, file_path)
            if ocr_text:
                pages.append((page_num, ocr_text))

    doc.close()
    return pages


def _ocr_pdf_page(page: Any, page_num: int, file_path: str) -> str:
    """
    Attempt pytesseract OCR on a single PDF page that has no text layer.

    Renders the page to a PIL image then feeds it to pytesseract.
    Returns an empty string if pytesseract is not installed or OCR
    produces no usable text — the pipeline continues without that page.
    """
    try:
        import io
        import pytesseract
        from PIL import Image
    except ImportError:
        logger.debug(
            "pytesseract/Pillow not installed — skipping OCR for page",
            page=page_num,
            file=file_path,
        )
        return ""

    try:
        import fitz
        mat = page.get_pixmap(matrix=fitz.Matrix(2, 2))
        img_bytes = mat.tobytes("png")
        image = Image.open(io.BytesIO(img_bytes))
        text = pytesseract.image_to_string(image).strip()
        if text:
            logger.info(
                "OCR extracted text from page",
                page=page_num,
                chars=len(text),
            )
        return text
    except Exception as exc:          # noqa: BLE001
        logger.warning(
            "OCR failed for page (non-fatal)",
            page=page_num,
            error=str(exc),
        )
        return ""


def _extract_docx(file_path: str) -> list[tuple[int, str]]:
    """
    Extract text from a DOCX file using python-docx.
    DOCX has no native pages — all text is returned as page 1.
    """
    try:
        from docx import Document as DocxDocument
    except ImportError as exc:
        raise RuntimeError("python-docx is not installed.") from exc

    doc = DocxDocument(file_path)
    paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
    if not paragraphs:
        return []
    return [(1, "\n".join(paragraphs))]


def _extract_xlsx(file_path: str) -> list[tuple[int, str]]:
    """
    Extract text from an XLSX file using openpyxl.
    Each worksheet is treated as a separate 'page'.
    """
    try:
        import openpyxl
    except ImportError as exc:
        raise RuntimeError("openpyxl is not installed.") from exc

    wb = openpyxl.load_workbook(file_path, read_only=True, data_only=True)
    pages: list[tuple[int, str]] = []
    for sheet_idx, sheet in enumerate(wb.worksheets, start=1):
        rows: list[str] = []
        for row in sheet.iter_rows(values_only=True):
            cells = [str(c) for c in row if c is not None and str(c).strip()]
            if cells:
                rows.append(" | ".join(cells))
        if rows:
            pages.append((sheet_idx, "\n".join(rows)))
    wb.close()
    return pages


def _extract_text(file_path: str, file_type: str) -> list[tuple[int, str]]:
    """Dispatch to the correct extractor based on file_type."""
    extractors = {
        "pdf":  _extract_pdf,
        "docx": _extract_docx,
        "xlsx": _extract_xlsx,
    }
    extractor = extractors.get(file_type)
    if not extractor:
        raise ValueError(f"Unsupported file type: {file_type}")
    return extractor(file_path)


# ── ChromaDB upsert ───────────────────────────────────────────────────────────

def _upsert_to_chroma(
    document_id: str,
    project_id: str,
    supplier_id: str | None,
    chunks: list[Any],         # list[TextChunk]
    embeddings: list[list[float]],
) -> None:
    """Upsert chunks + embeddings into the document_chunks ChromaDB collection."""
    from app.database.chroma import get_document_chunks_collection

    collection = get_document_chunks_collection()

    ids: list[str] = []
    documents: list[str] = []
    metadatas: list[dict] = []

    for chunk, embedding in zip(chunks, embeddings):
        chunk_id = str(uuid.uuid4())
        ids.append(chunk_id)
        documents.append(chunk.content)
        metadatas.append({
            "document_id":  document_id,
            "project_id":   project_id,
            "supplier_id":  supplier_id or "",
            "page_number":  chunk.page_number,
            "section_name": chunk.section_name or "",
            "chunk_index":  chunk.chunk_index,
            "token_count":  chunk.token_count,
        })

    if ids:
        collection.upsert(
            ids=ids,
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas,
        )
        logger.info(
            "ChromaDB upsert complete",
            document_id=document_id,
            chunks=len(ids),
        )


# ── Main Celery task ──────────────────────────────────────────────────────────

@celery_app.task(
    bind=True,
    name="app.workers.document_worker.process_document",
    max_retries=3,
    default_retry_delay=10,
    acks_late=True,
)
def process_document(self, document_id: str) -> dict:
    """
    Full document processing pipeline.

    Parameters
    ----------
    document_id:
        UUID string of the Document row created during upload.

    Returns
    -------
    dict with ``status`` and ``chunk_count`` keys, stored in Redis.
    """
    logger.info("process_document started", document_id=document_id, task_id=self.request.id)

    # ── 1. Load document record (sync psycopg2) ───────────────────────────────
    doc = _load_document(document_id)
    if not doc:
        logger.error("Document not found", document_id=document_id)
        return {"status": S_ERROR, "chunk_count": 0, "error": "Document not found"}

    file_path   = doc["file_path"]
    file_type   = doc["file_type"]
    project_id  = doc["project_id"]
    supplier_id = doc["supplier_id"]

    # ── 2. Mark processing ────────────────────────────────────────────────────
    _set_status(document_id, S_PROCESSING)

    try:
        # ── 3. Extract text (+ OCR fallback for image-only PDFs) ─────────────
        _set_status(document_id, S_EXTRACTING)
        logger.info("Extracting text", document_id=document_id, file_type=file_type)

        if not Path(file_path).exists():
            # Fallback: retrieve file bytes from Redis if uploaded on another host (e.g. Vercel)
            try:
                import redis
                from app.core.config import settings

                r_client = redis.from_url(settings.redis_url)
                cached_bytes = r_client.get(f"doc_bytes:{document_id}")
                r_client.close()

                if cached_bytes:
                    Path(file_path).parent.mkdir(parents=True, exist_ok=True)
                    Path(file_path).write_bytes(cached_bytes)
                    logger.info("Restored document bytes from Redis fallback", document_id=document_id)
            except Exception as exc:
                logger.warning("Failed to retrieve document bytes from Redis fallback", document_id=document_id, error=str(exc))

        if not Path(file_path).exists():
            raise FileNotFoundError(f"File not found on disk: {file_path}")

        pages = _extract_text(file_path, file_type)
        if not pages:
            raise ValueError("No text could be extracted from the document.")

        logger.info(
            "Text extracted",
            document_id=document_id,
            pages=len(pages),
            chars=sum(len(t) for _, t in pages),
        )

        # ── 4. Semantic chunking ──────────────────────────────────────────────
        from app.utils.chunker import chunk_pages
        chunks = chunk_pages(pages)
        logger.info("Chunking complete", document_id=document_id, chunks=len(chunks))

        if not chunks:
            raise ValueError("Chunker produced zero chunks.")

        # ── 5. Embed + index in ChromaDB ──────────────────────────────────────
        _set_status(document_id, S_INDEXING)
        texts = [c.content for c in chunks]

        from app.ai.embeddings import embed_texts

        all_embeddings: list[list[float]] = []
        batch_size = 100
        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            all_embeddings.extend(embed_texts(batch))

        _upsert_to_chroma(document_id, project_id, supplier_id, chunks, all_embeddings)

        # ── 6. Persist chunks to PostgreSQL (sync) ────────────────────────────
        _save_chunks(document_id, chunks)

        # ── 6.5 Extract supplier data if applicable ────────────────────────────
        if supplier_id:
            # Join chunks up to ~10,000 characters to fit in LLM context well
            full_text = "\n\n".join(c.content for c in chunks)[:15000]
            _extract_and_update_supplier_sync(supplier_id, full_text)

        # ── 7. Invalidate stale Redis caches ──────────────────────────────────
        _invalidate_caches(project_id)

        # ── 8. Mark completed ─────────────────────────────────────────────────
        _set_status(document_id, S_COMPLETED)
        logger.info(
            "process_document completed",
            document_id=document_id,
            chunks=len(chunks),
        )

        return {"status": S_COMPLETED, "chunk_count": len(chunks), "error": None}

    except Exception as exc:
        logger.error(
            "process_document failed",
            document_id=document_id,
            error=str(exc),
            exc_info=exc,
        )
        _set_status(document_id, S_ERROR)

        try:
            raise self.retry(exc=exc)
        except self.MaxRetriesExceededError:
            return {"status": S_ERROR, "chunk_count": 0, "error": str(exc)}
