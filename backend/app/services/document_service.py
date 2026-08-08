"""Document business service — orchestrates upload, validation, and task dispatch."""

import math
from pathlib import Path

from app.core.config import settings
from app.core.logging import get_logger
from app.models.document import Document
from app.repositories.document_repository import DocumentRepository
from app.schemas.common import PaginationMeta
from app.schemas.document import (
    DocumentListSchema,
    DocumentStatusResponse,
    DocumentSummarySchema,
    DocumentUploadResponse,
    JobStatusResponse,
)
from app.utils.file_validator import validate_upload
from app.utils.sanitizer import sanitize_filename, storage_filename

logger = get_logger(__name__)


# ── Status → progress mapping ─────────────────────────────────────────────────

_STATUS_PROGRESS: dict[str, int] = {
    "uploaded":   5,
    "processing": 20,
    "extracting": 50,
    "indexing":   80,
    "completed": 100,
    "error":       0,
}


class DocumentService:
    def __init__(self, document_repo: DocumentRepository) -> None:
        self.document_repo = document_repo

    # ── Upload ────────────────────────────────────────────────────────────────

    async def upload(
        self,
        file_bytes: bytes,
        original_filename: str,
        project_id: str,
        supplier_id: str | None = None,
    ) -> DocumentUploadResponse:
        """
        Validate, save, persist, and enqueue a document for processing.

        Raises
        ------
        ValueError
            If the file fails validation (size, extension, magic bytes).
        """
        # 1. Validate
        validation = validate_upload(file_bytes, original_filename)
        if not validation.valid:
            raise ValueError(f"{validation.error_code}: {validation.error_message}")

        # 2. Build safe storage filename and write to disk
        safe_name = storage_filename(original_filename)
        upload_path = Path(settings.upload_dir) / safe_name
        upload_path.parent.mkdir(parents=True, exist_ok=True)
        upload_path.write_bytes(file_bytes)

        logger.info(
            "File saved",
            original=original_filename,
            storage=safe_name,
            size=validation.file_size_bytes,
        )

        # 3. Persist Document row
        display_name = sanitize_filename(original_filename)
        document = Document(
            filename=display_name,
            file_path=str(upload_path),
            file_type=validation.file_type,
            file_size_bytes=validation.file_size_bytes,
            sha256_checksum=validation.sha256_checksum,
            status="uploaded",
            project_id=project_id,
            supplier_id=supplier_id,
        )
        saved = await self.document_repo.create(document)
        await self.document_repo.session.commit()

        # 4. Enqueue Celery task
        from app.workers.document_worker import process_document
        task = process_document.delay(saved.id)

        logger.info(
            "Processing task enqueued",
            document_id=saved.id,
            task_id=task.id,
        )

        return DocumentUploadResponse(
            document_id=saved.id,
            filename=display_name,
            file_type=validation.file_type,
            file_size_bytes=validation.file_size_bytes,
            status="uploaded",
            job_id=task.id,
        )

    # ── Status / polling ──────────────────────────────────────────────────────

    async def get_status(self, document_id: str) -> DocumentStatusResponse | None:
        doc = await self.document_repo.get_by_id_slim(document_id)
        if not doc:
            return None
        chunk_count = await self.document_repo.count_chunks(document_id)
        return DocumentStatusResponse(
            document_id=doc.id,
            filename=doc.filename,
            status=doc.status,
            progress=_STATUS_PROGRESS.get(doc.status, 0),
            chunk_count=chunk_count,
            created_at=doc.created_at,
            updated_at=doc.updated_at,
        )

    async def get_job_status(self, job_id: str, document_id: str) -> JobStatusResponse:
        """
        Combine Celery task state with the Document.status for a richer
        polling response.
        """
        from celery.result import AsyncResult
        from app.workers.celery_app import celery_app

        result = AsyncResult(job_id, app=celery_app)
        celery_state = result.state   # PENDING | STARTED | SUCCESS | FAILURE | RETRY

        doc = await self.document_repo.get_by_id_slim(document_id)
        if not doc:
            return JobStatusResponse(
                job_id=job_id,
                document_id=document_id,
                status="pending",
                progress=0,
                detail="Document record not found.",
            )

        db_status = doc.status
        progress = _STATUS_PROGRESS.get(db_status, 0)

        detail_map = {
            "uploaded":   "Waiting for worker to pick up.",
            "processing": "Worker started processing.",
            "extracting": "Extracting text from document.",
            "indexing":   "Generating embeddings and indexing.",
            "completed":  "Processing complete.",
            "error":      "Processing failed.",
        }

        error = None
        if celery_state == "FAILURE":
            error = str(result.result) if result.result else "Unknown error"

        return JobStatusResponse(
            job_id=job_id,
            document_id=document_id,
            status=db_status,
            progress=progress,
            detail=detail_map.get(db_status, ""),
            error=error,
        )

    # ── List ──────────────────────────────────────────────────────────────────

    async def list_documents(
        self,
        project_id: str,
        *,
        page: int = 1,
        limit: int = 20,
    ) -> tuple[list[DocumentSummarySchema], PaginationMeta]:
        offset = (page - 1) * limit
        docs = await self.document_repo.list_by_project(
            project_id, limit=limit, offset=offset
        )
        total = await self.document_repo.count_by_project(project_id)

        items: list[DocumentSummarySchema] = []
        for doc in docs:
            chunk_count = len(doc.chunks) if doc.chunks else 0
            items.append(
                DocumentSummarySchema(
                    id=doc.id,
                    filename=doc.filename,
                    file_type=doc.file_type,
                    file_size_bytes=doc.file_size_bytes,
                    status=doc.status,
                    chunk_count=chunk_count,
                    supplier_id=doc.supplier_id,
                    created_at=doc.created_at,
                )
            )

        meta = PaginationMeta(
            page=page,
            limit=limit,
            total=total,
            total_pages=max(1, math.ceil(total / limit)) if total else 0,
        )
        return items, meta

    async def get_verification_queue(
        self,
        project_id: str,
        limit: int = 50,
    ) -> list[dict]:
        """Fetch global queue of document chunks sorted by lowest confidence."""
        chunks = await self.document_repo.get_verification_queue(project_id, limit=limit)
        
        # Serialize to dict including the parent document filename
        results = []
        for c in chunks:
            results.append({
                "id": c.id,
                "document_id": c.document_id,
                "document_filename": c.document.filename if c.document else "Unknown",
                "chunk_index": c.chunk_index,
                "page_number": c.page_number,
                "section_name": c.section_name,
                "content": c.content,
                "token_count": c.token_count,
                "extraction_confidence": c.extraction_confidence,
                "created_at": c.created_at,
            })
        return results

    # ── Delete ────────────────────────────────────────────────────────────────

    async def delete(self, document_id: str) -> bool:
        doc = await self.document_repo.get_by_id_slim(document_id)
        if not doc:
            return False

        # Remove file from disk (best-effort)
        try:
            file_path = Path(doc.file_path)
            if file_path.exists():
                file_path.unlink()
        except OSError as exc:
            logger.warning("Could not delete file from disk", path=doc.file_path, error=str(exc))

        await self.document_repo.delete(doc)
        return True
