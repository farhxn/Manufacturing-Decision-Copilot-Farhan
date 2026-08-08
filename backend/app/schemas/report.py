"""Report API schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class ReportGenerateRequest(BaseModel):
    project_id: str = Field(default="00000000-0000-4000-a000-000000000002")
    report_type: str = Field(default="executive", description="executive | risk | technical")
    title: str | None = Field(default=None, description="Override auto-generated title")


class ReportSummarySchema(BaseModel):
    id: str
    title: str
    report_type: str
    project_id: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ReportDetailSchema(ReportSummarySchema):
    summary_text: str


class ReportDownloadSchema(BaseModel):
    """Payload returned when downloading a report as plain-text."""
    id: str
    title: str
    content: str
    filename: str
