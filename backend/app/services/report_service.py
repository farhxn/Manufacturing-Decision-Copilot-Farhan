"""
Report business service.

Generates an executive/risk/technical report text from the current
recommendation + supplier ranking and persists it to PostgreSQL.
Downloading returns the stored summary_text as a formatted plain-text
document — no external PDF library required for the hackathon demo.
"""

from __future__ import annotations

from datetime import datetime, timezone

from app.models.report import Report
from app.repositories.project_repository import ProjectRepository
from app.repositories.recommendation_repository import RecommendationRepository
from app.repositories.report_repository import ReportRepository
from app.repositories.supplier_repository import SupplierRepository
from app.schemas.report import ReportDetailSchema, ReportDownloadSchema, ReportSummarySchema
from app.services.recommendation_service import RecommendationService
from app.services.supplier_mapper import (
    DEFAULT_REQUIRED_CAPABILITIES,
    DEFAULT_REQUIRED_CERTS,
    project_to_weights,
    suppliers_to_inputs,
)
from app.core.logging import get_logger
from app.ai.client import build_agent, run_agent
from app.ai.schemas import ExecutiveSummary
from app.ai.prompts.v1.executive_summary import SYSTEM_PROMPT, build_user_prompt
import json

logger = get_logger(__name__)

_SEPARATOR = "═" * 60


def _build_report_text(
    project_name: str,
    report_type: str,
    rec,           # RecommendationSchema
    generated_at: str,
) -> str:
    """Render the report as a structured plain-text document."""
    lines: list[str] = [
        "MANUFACTURING DECISION COPILOT",
        f"{'Executive Procurement Report' if report_type == 'executive' else report_type.title() + ' Report'}",
        f"Generated : {generated_at}",
        f"Project   : {project_name}",
        _SEPARATOR,
        "",
        "RECOMMENDATION",
        _SEPARATOR,
        f"Recommended Supplier : {rec.recommended_supplier_name}",
        f"Confidence           : {rec.confidence_score:.1f}% ({rec.confidence_label})",
        "",
        "SUMMARY",
        rec.summary,
        "",
    ]

    if rec.pros:
        lines += ["STRENGTHS"] + [f"  • {p}" for p in rec.pros] + [""]
    if rec.cons:
        lines += ["CONCERNS"] + [f"  • {c}" for c in rec.cons] + [""]
    if rec.tradeoffs:
        lines += ["TRADEOFFS"] + [f"  • {t}" for t in rec.tradeoffs] + [""]
    if rec.risks:
        lines += ["RISKS"] + [f"  • {r}" for r in rec.risks] + [""]
    if rec.assumptions:
        lines += ["ASSUMPTIONS"] + [f"  • {a}" for a in rec.assumptions] + [""]
    if rec.next_actions:
        lines += ["NEXT ACTIONS"] + [f"  • {a}" for a in rec.next_actions] + [""]

    lines += [
        _SEPARATOR,
        "SUPPLIER RANKING",
        _SEPARATOR,
    ]
    for r in rec.ranking:
        lines.append(
            f"  #{r.rank:>2}  {r.supplier_name:<35} ({r.country})"
            f"  Score: {r.final_score:>5.1f}/100"
            f"  Landed: ${r.scores.landed_cost:>8.2f}"
        )

    lines += [
        "",
        _SEPARATOR,
        "CONFIDENCE DETAIL",
        _SEPARATOR,
        rec.confidence_explanation,
        "",
        "AI Narrative : " + ("Yes" if rec.ai_narrative else "No (deterministic)"),
        f"Evidence IDs : {len(rec.evidence_ids)}",
        "",
        _SEPARATOR,
        "DISCLAIMER",
        _SEPARATOR,
        "This analysis is AI-assisted decision support.",
        "Legal, regulatory, and engineering advice requires human expert verification.",
    ]

    return "\n".join(lines)


class ReportService:
    def __init__(
        self,
        report_repo: ReportRepository,
        project_repo: ProjectRepository,
        recommendation_service: RecommendationService,
    ) -> None:
        self._report_repo = report_repo
        self._project_repo = project_repo
        self._recommendation_service = recommendation_service

    # ── Generate ──────────────────────────────────────────────────────────────

    async def generate(
        self,
        project_id: str,
        report_type: str = "executive",
        title: str | None = None,
    ) -> ReportDetailSchema:
        project = await self._project_repo.get_by_id(project_id)
        project_name = project.name if project else "Motor Housing Sourcing Project"

        rec = await self._recommendation_service.get_recommendation(project_id)
        if not rec:
            raise ValueError(f"No recommendation available for project {project_id}.")

        generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        auto_title = title or (
            f"{project_name} — {report_type.title()} Report — {datetime.now(timezone.utc).strftime('%Y-%m-%d')}"
        )
        
        # Build scores table string for the prompt
        scores_table_lines = []
        for r in rec.ranking:
            scores_table_lines.append(f"#{r.rank} {r.supplier_name} ({r.country}): {r.final_score:.1f}/100")
        scores_table = "\n".join(scores_table_lines)
        
        # Build prompt and run agent
        user_prompt = build_user_prompt(
            project_name=project_name,
            recommended_supplier=rec.recommended_supplier_name,
            recommended_supplier_country=rec.ranking[0].country if rec.ranking else "Unknown",
            top_score=rec.ranking[0].final_score if rec.ranking else 0.0,
            runner_up=rec.ranking[1].supplier_name if len(rec.ranking) > 1 else "None",
            supplier_count=len(rec.ranking),
            document_count=len(rec.evidence_ids), # Approx count
            scores_table=scores_table,
            key_risks=rec.risks,
            scenario_summary=None,
        )
        
        agent = build_agent(ExecutiveSummary, SYSTEM_PROMPT)
        try:
            ai_summary = await run_agent(agent, user_prompt)
            summary_text = ai_summary.model_dump_json()
        except Exception as e:
            logger.error("ExecutiveSummaryAgent failed, falling back to deterministic", error=str(e))
            summary_text = _build_report_text(project_name, report_type, rec, generated_at)

        record = Report(
            title=auto_title,
            report_type=report_type,
            summary_text=summary_text,
            project_id=project_id,
        )
        saved = await self._report_repo.create(record)

        logger.info(
            "Report generated",
            report_id=saved.id,
            project_id=project_id,
            report_type=report_type,
        )

        return ReportDetailSchema(
            id=saved.id,
            title=saved.title,
            report_type=saved.report_type,
            project_id=saved.project_id,
            summary_text=saved.summary_text,
            created_at=saved.created_at,
        )

    # ── List ──────────────────────────────────────────────────────────────────

    async def list_reports(
        self,
        project_id: str,
        limit: int = 20,
    ) -> list[ReportSummarySchema]:
        reports = await self._report_repo.list_by_project(project_id, limit=limit)
        return [
            ReportSummarySchema(
                id=r.id,
                title=r.title,
                report_type=r.report_type,
                project_id=r.project_id,
                created_at=r.created_at,
            )
            for r in reports
        ]

    # ── Download ──────────────────────────────────────────────────────────────

    async def download(self, report_id: str) -> ReportDownloadSchema | None:
        report = await self._report_repo.get_by_id(report_id)
        if not report:
            return None

        safe_title = report.title.replace(" ", "_").replace("/", "-")[:60]
        filename = f"MDC_Report_{safe_title}_{report.id[:8]}.txt"

        return ReportDownloadSchema(
            id=report.id,
            title=report.title,
            content=report.summary_text,
            filename=filename,
        )
