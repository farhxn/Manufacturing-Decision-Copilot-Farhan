"""Document API routes.

Endpoints
---------
POST /documents/upload             — multipart file upload, returns job_id
GET  /documents                    — paginated document list for a project
GET  /documents/{id}               — single document status + progress
GET  /documents/{id}/chunks        — list extracted chunks
GET  /documents/{id}/file          — stream raw file bytes (PDF/DOCX/XLSX)
GET  /jobs/{id}                    — Celery job polling (job_id + document_id)
DELETE /documents/{id}             — delete document + file from disk
"""

from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile
from fastapi.responses import FileResponse

from app.core.dependencies import get_document_service
from app.core.exceptions import AppHTTPException
from app.schemas.common import APIResponse, PaginationMeta
from app.schemas.document import (
    DocumentListSchema,
    DocumentStatusResponse,
    DocumentSummarySchema,
    DocumentUploadResponse,
    JobStatusResponse,
    DocumentChunkSchema,
    DocumentChunkWithMetaSchema,
)
from app.services.document_service import DocumentService

router = APIRouter(tags=["Documents"])

DEFAULT_PROJECT_ID = "00000000-0000-4000-a000-000000000002"


# ── Upload ────────────────────────────────────────────────────────────────────

@router.post(
    "/documents/upload",
    response_model=APIResponse[DocumentUploadResponse],
    status_code=201,
    summary="Upload a document for processing",
)
async def upload_document(
    file: UploadFile = File(..., description="PDF, DOCX, or XLSX file (max 50 MB)"),
    project_id: str = Form(DEFAULT_PROJECT_ID),
    supplier_id: str | None = Form(None),
    service: DocumentService = Depends(get_document_service),
):
    file_bytes = await file.read()
    try:
        result = await service.upload(
            file_bytes=file_bytes,
            original_filename=file.filename or "upload.bin",
            project_id=project_id,
            supplier_id=supplier_id or None,
        )
    except ValueError as exc:
        raise AppHTTPException(
            status_code=422,
            code="DOCUMENT_UPLOAD_FAILED",
            message=str(exc),
        ) from exc

    return APIResponse(
        success=True,
        message="Document uploaded and queued for processing.",
        data=result,
    )


# ── List ──────────────────────────────────────────────────────────────────────

@router.get(
    "/documents",
    response_model=APIResponse[list[DocumentSummarySchema]],
    summary="List documents for a project",
)
async def list_documents(
    project_id: str = Query(DEFAULT_PROJECT_ID),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    service: DocumentService = Depends(get_document_service),
):
    items, meta = await service.list_documents(project_id, page=page, limit=limit)
    return APIResponse(
        success=True,
        message="Documents retrieved successfully.",
        data=items,
        meta=meta,
    )


# ── Single document status ────────────────────────────────────────────────────

@router.get(
    "/documents/{document_id}",
    response_model=APIResponse[DocumentStatusResponse],
    summary="Get document processing status",
)
async def get_document_status(
    document_id: str,
    service: DocumentService = Depends(get_document_service),
):
    status = await service.get_status(document_id)
    if not status:
        raise AppHTTPException(
            status_code=404,
            code="DOCUMENT_NOT_FOUND",
            message=f"Document {document_id} was not found.",
        )
    return APIResponse(
        success=True,
        message="Document status retrieved successfully.",
        data=status,
    )


# ── Chunks ────────────────────────────────────────────────────────────────────

@router.get(
    "/documents/{document_id}/chunks",
    response_model=APIResponse[list[DocumentChunkSchema]],
    summary="List extracted text chunks for a document",
)
async def get_document_chunks(
    document_id: str,
    service: DocumentService = Depends(get_document_service),
):
    doc = await service.document_repo.get_by_id(document_id)
    if not doc:
        raise AppHTTPException(
            status_code=404,
            code="DOCUMENT_NOT_FOUND",
            message=f"Document {document_id} was not found.",
        )
    chunks = await service.document_repo.get_chunks(document_id)
    data = [
        DocumentChunkSchema(
            id=c.id,
            document_id=c.document_id,
            chunk_index=c.chunk_index,
            page_number=c.page_number,
            section_name=c.section_name,
            content=c.content,
            token_count=c.token_count,
            extraction_confidence=c.extraction_confidence,
        )
        for c in chunks
    ]
    return APIResponse(
        success=True,
        message=f"{len(data)} chunks retrieved.",
        data=data,
    )

# ── Global Verification Queue ─────────────────────────────────────────────────

@router.get(
    "/documents/claims/queue",
    response_model=APIResponse[list[DocumentChunkWithMetaSchema]],
    summary="List all extracted text chunks for a project, sorted by confidence ascending",
)
async def get_verification_queue(
    project_id: str = Query(DEFAULT_PROJECT_ID),
    limit: int = Query(50, ge=1, le=100),
    service: DocumentService = Depends(get_document_service),
):
    chunks = await service.get_verification_queue(project_id, limit=limit)
    return APIResponse(
        success=True,
        message="Verification queue retrieved.",
        data=chunks,
    )


# ── File download / stream ────────────────────────────────────────────────────

@router.get(
    "/documents/{document_id}/file",
    summary="Stream the raw uploaded file (PDF/DOCX/XLSX) for the PDF viewer",
    response_class=FileResponse,
)
async def get_document_file(
    document_id: str,
    service: DocumentService = Depends(get_document_service),
):
    doc = await service.document_repo.get_by_id_slim(document_id)
    if not doc:
        raise AppHTTPException(
            status_code=404,
            code="DOCUMENT_NOT_FOUND",
            message=f"Document {document_id} was not found.",
        )

    file_path = Path(doc.file_path)
    if not file_path.exists():
        raise AppHTTPException(
            status_code=404,
            code="FILE_NOT_ON_DISK",
            message=f"File for document {document_id} is not available on disk.",
        )

    # Map stored extension to media type
    media_map = {
        ".pdf":  "application/pdf",
        ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    }
    media_type = media_map.get(file_path.suffix.lower(), "application/octet-stream")

    return FileResponse(
        path=str(file_path),
        media_type=media_type,
        filename=doc.filename,
        headers={
            # Allow pdfjs-dist running at localhost:3000 to load the file
            "Access-Control-Allow-Origin": "*",
            "Cache-Control": "no-store",
        },
    )


# ── Job polling ───────────────────────────────────────────────────────────────

@router.get(
    "/jobs/{job_id}",
    response_model=APIResponse[JobStatusResponse],
    summary="Poll a document processing job by Celery task ID",
)
async def get_job_status(
    job_id: str,
    document_id: str = Query(..., description="Document ID associated with this job"),
    service: DocumentService = Depends(get_document_service),
):
    result = await service.get_job_status(job_id, document_id)
    return APIResponse(
        success=True,
        message="Job status retrieved.",
        data=result,
    )


# ── Delete ────────────────────────────────────────────────────────────────────

@router.delete(
    "/documents/{document_id}",
    status_code=204,
    summary="Delete a document and its extracted data",
)
async def delete_document(
    document_id: str,
    service: DocumentService = Depends(get_document_service),
):
    deleted = await service.delete(document_id)
    if not deleted:
        raise AppHTTPException(
            status_code=404,
            code="DOCUMENT_NOT_FOUND",
            message=f"Document {document_id} was not found.",
        )
