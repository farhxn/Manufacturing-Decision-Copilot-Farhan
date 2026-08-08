"""Reports API routes.

Endpoints
---------
POST /reports/generate          — generate + persist a report, return full detail
GET  /reports                   — list saved reports for a project
GET  /reports/{id}/download     — return report detail as JSON (PDF rendered client-side)
DELETE /reports/{id}            — delete a report record
"""

from fastapi import APIRouter, Depends, Query

from app.core.dependencies import get_report_service
from app.core.exceptions import AppHTTPException
from app.schemas.common import APIResponse
from app.schemas.report import (
    ReportDetailSchema,
    ReportGenerateRequest,
    ReportSummarySchema,
)
from app.services.report_service import ReportService

router = APIRouter(prefix="/reports", tags=["Reports"])

DEFAULT_PROJECT_ID = "00000000-0000-4000-a000-000000000002"


# ── Generate ──────────────────────────────────────────────────────────────────

@router.post(
    "/generate",
    response_model=APIResponse[ReportDetailSchema],
    status_code=201,
    summary="Generate and persist an executive report",
)
async def generate_report(
    body: ReportGenerateRequest,
    service: ReportService = Depends(get_report_service),
):
    try:
        report = await service.generate(
            project_id=body.project_id,
            report_type=body.report_type,
            title=body.title,
        )
    except ValueError as exc:
        raise AppHTTPException(
            status_code=422,
            code="REPORT_GENERATION_FAILED",
            message=str(exc),
        ) from exc

    return APIResponse(
        success=True,
        message="Report generated successfully.",
        data=report,
    )


# ── List ──────────────────────────────────────────────────────────────────────

@router.get(
    "",
    response_model=APIResponse[list[ReportSummarySchema]],
    summary="List saved reports for a project",
)
async def list_reports(
    project_id: str = Query(DEFAULT_PROJECT_ID),
    limit: int = Query(20, ge=1, le=100),
    service: ReportService = Depends(get_report_service),
):
    reports = await service.list_reports(project_id=project_id, limit=limit)
    return APIResponse(
        success=True,
        message=f"{len(reports)} report(s) retrieved.",
        data=reports,
    )


# ── Download ──────────────────────────────────────────────────────────────────

@router.get(
    "/{report_id}/download",
    response_model=APIResponse[ReportDetailSchema],
    summary="Fetch full report data for client-side PDF rendering",
)
async def download_report(
    report_id: str,
    service: ReportService = Depends(get_report_service),
):
    """
    Returns the full report detail as JSON.
    The frontend uses @react-pdf/renderer to render the PDF in the browser —
    no binary file generation happens on the server.
    """
    result = await service.download(report_id)
    if not result:
        raise AppHTTPException(
            status_code=404,
            code="REPORT_NOT_FOUND",
            message=f"Report {report_id} was not found.",
        )
    # Fetch the full detail (summary_text included) for the client
    report = await service._report_repo.get_by_id(report_id)
    detail = ReportDetailSchema(
        id=report.id,
        title=report.title,
        report_type=report.report_type,
        project_id=report.project_id,
        summary_text=report.summary_text,
        created_at=report.created_at,
    )
    return APIResponse(
        success=True,
        message="Report data retrieved for download.",
        data=detail,
    )


# ── Delete ────────────────────────────────────────────────────────────────────

@router.delete(
    "/{report_id}",
    status_code=204,
    summary="Delete a report record",
)
async def delete_report(
    report_id: str,
    service: ReportService = Depends(get_report_service),
):
    deleted = await service._report_repo.delete(report_id)
    if not deleted:
        raise AppHTTPException(
            status_code=404,
            code="REPORT_NOT_FOUND",
            message=f"Report {report_id} was not found.",
        )
