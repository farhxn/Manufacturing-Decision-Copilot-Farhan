"""Document API schemas."""

from datetime import datetime

from pydantic import BaseModel, Field


# ── Upload / response shapes ──────────────────────────────────────────────────

class DocumentUploadResponse(BaseModel):
    """Returned immediately after a successful file upload."""
    document_id: str
    filename: str
    file_type: str
    file_size_bytes: int
    status: str                      # "uploaded"
    job_id: str                      # Celery task ID for polling


class DocumentStatusResponse(BaseModel):
    """Polling response for a single document's processing state."""
    document_id: str
    filename: str
    status: str                      # uploaded | processing | extracting | indexing | completed | error
    progress: int = Field(ge=0, le=100)   # 0-100
    error_message: str | None = None
    chunk_count: int = 0
    created_at: datetime
    updated_at: datetime


class DocumentSummarySchema(BaseModel):
    """Brief document entry for list views."""
    id: str
    filename: str
    file_type: str
    file_size_bytes: int
    status: str
    chunk_count: int = 0
    supplier_id: str | None = None
    created_at: datetime


class DocumentListSchema(BaseModel):
    """Paginated list of documents."""
    items: list[DocumentSummarySchema] = Field(default_factory=list)
    total: int = 0


# ── Chunk schema ──────────────────────────────────────────────────────────────

class DocumentChunkSchema(BaseModel):
    """A single extracted text chunk, as stored in PostgreSQL."""
    id: str
    document_id: str
    chunk_index: int
    page_number: int
    section_name: str | None = None
    content: str
    token_count: int
    extraction_confidence: float

class DocumentChunkWithMetaSchema(DocumentChunkSchema):
    """Chunk with metadata (like document filename)."""
    document_filename: str
    created_at: datetime


# ── Job status (Celery task) ──────────────────────────────────────────────────

class JobStatusResponse(BaseModel):
    """
    Lightweight job-tracking response.

    Maps to the Celery task result stored in Redis.
    Mirrors the Document.status field so the frontend can use either
    endpoint for polling.
    """
    job_id: str
    document_id: str
    status: str          # pending | processing | extracting | indexing | completed | failed
    progress: int = Field(ge=0, le=100)
    detail: str = ""     # human-readable current step description
    error: str | None = None
