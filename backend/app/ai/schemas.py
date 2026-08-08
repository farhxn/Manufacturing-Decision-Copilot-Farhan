"""
PydanticAI output schemas.

All agents must return one of these schemas.  The receiving service
validates the output and rejects it if the schema is violated.

CRITICAL rules (from roadmap):
- Confidence PERCENTAGE is calculated by ConfidenceEngine — NEVER by an LLM.
  `confidence_explanation` is narrative text only.
- `evidence_ids` are ChromaDB chunk IDs returned by the retriever;
  the agent must select from the chunks it was given, not invent new IDs.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


# ── Recommendation agent output ───────────────────────────────────────────────

class RecommendationOutput(BaseModel):
    """Output schema for RecommendationAgent."""

    recommendation: str = Field(
        description="One-sentence recommendation naming the top supplier."
    )
    summary: str = Field(
        description="2-4 sentence executive summary of the recommendation."
    )
    confidence_explanation: str = Field(
        description="Narrative explanation of confidence factors — NOT a number."
    )
    pros: list[str] = Field(
        default_factory=list,
        description="Key strengths of the recommended supplier (3-5 bullets).",
    )
    cons: list[str] = Field(
        default_factory=list,
        description="Known weaknesses or concerns (2-4 bullets).",
    )
    tradeoffs: list[str] = Field(
        default_factory=list,
        description="Trade-off statements comparing top vs runner-up (2-3 bullets).",
    )
    risks: list[str] = Field(
        default_factory=list,
        description="Risk factors that could invalidate this recommendation (2-4 bullets).",
    )
    assumptions: list[str] = Field(
        default_factory=list,
        description="Assumptions underlying this analysis (2-3 bullets).",
    )
    limitations: list[str] = Field(
        default_factory=list,
        description="Limitations of available data or analysis (1-3 bullets).",
    )
    next_actions: list[str] = Field(
        default_factory=list,
        description="Concrete next steps for the procurement team (2-4 bullets).",
    )
    evidence_ids: list[str] = Field(
        default_factory=list,
        description=(
            "Chunk IDs (from the provided evidence list) that support this recommendation. "
            "Only include IDs from the evidence you were given."
        ),
    )


# ── Scenario explainer output ─────────────────────────────────────────────────

class ScenarioExplanation(BaseModel):
    """Output schema for ScenarioExplainerAgent."""

    headline: str = Field(
        description="One sentence: what changed and who benefits most."
    )
    explanation: str = Field(
        description=(
            "2-4 sentence plain-English explanation of why the ranking changed "
            "under this scenario."
        )
    )
    key_drivers: list[str] = Field(
        default_factory=list,
        description="The 2-3 most important factors driving the ranking change.",
    )
    winner_rationale: str = Field(
        description="Why the new top supplier benefits from this scenario."
    )
    loser_rationale: str = Field(
        description="Why the previous top supplier is now disadvantaged.",
    )
    caveats: list[str] = Field(
        default_factory=list,
        description="Any important caveats or assumptions for this scenario.",
    )


# ── Executive summary output ──────────────────────────────────────────────────

class ExecutiveSummary(BaseModel):
    """Output schema for ExecutiveSummaryAgent (board-ready report)."""

    title: str = Field(description="Report title.")
    executive_summary: str = Field(
        description="3-5 sentence board-ready summary of the procurement decision."
    )
    recommendation_statement: str = Field(
        description="One-paragraph formal recommendation statement."
    )
    key_findings: list[str] = Field(
        default_factory=list,
        description="3-5 key findings from the analysis.",
    )
    risk_summary: list[str] = Field(
        default_factory=list,
        description="Top 3 risks to be aware of.",
    )
    next_steps: list[str] = Field(
        default_factory=list,
        description="3-5 concrete next steps for leadership.",
    )
    disclaimer: str = Field(
        default=(
            "This analysis is AI-assisted decision support. "
            "Legal, regulatory, and engineering advice requires human expert verification."
        ),
        description="Standard disclaimer for AI-generated procurement analysis.",
    )


# ── Comparison agent output ───────────────────────────────────────────────────

class ComparisonOutput(BaseModel):
    """Output schema for ComparisonAgent (two-supplier head-to-head)."""

    supplier_a_name: str
    supplier_b_name: str
    winner: str = Field(description="Name of the recommended supplier.")
    winner_rationale: str = Field(
        description="2-3 sentence rationale for the winner."
    )
    head_to_head: list[str] = Field(
        default_factory=list,
        description="Bullet-point comparison of key dimensions (cost, quality, risk, etc.).",
    )
    supplier_a_strengths: list[str] = Field(default_factory=list)
    supplier_a_weaknesses: list[str] = Field(default_factory=list)
    supplier_b_strengths: list[str] = Field(default_factory=list)
    supplier_b_weaknesses: list[str] = Field(default_factory=list)
    evidence_ids: list[str] = Field(
        default_factory=list,
        description="Chunk IDs supporting this comparison.",
    )


# ── Extraction agent output ───────────────────────────────────────────────────

class SupplierExtraction(BaseModel):
    """
    Output schema for ExtractionAgent.

    Structured data extracted from a supplier document chunk.
    All fields are optional — the agent only populates what it can
    confidently identify from the provided text.
    """

    supplier_name: str | None = None
    quoted_price: float | None = Field(
        default=None,
        description="Unit price in the document's stated currency.",
    )
    currency: str | None = Field(default=None, description="ISO 4217 currency code.")
    lead_time_days: int | None = None
    shipping_cost: float | None = None
    incoterms: str | None = Field(
        default=None, description="e.g. FOB, CIF, DDP."
    )
    certifications: list[str] = Field(
        default_factory=list,
        description="Certification names explicitly mentioned (e.g. ISO 9001, AS9100D).",
    )
    capabilities: list[str] = Field(
        default_factory=list,
        description="Manufacturing capabilities explicitly mentioned.",
    )
    defect_rate: float | None = Field(
        default=None,
        description="Defect rate as a percentage (e.g. 0.1 means 0.1%).",
    )
    on_time_delivery_pct: float | None = None
    production_capacity_pct: float | None = None
    confidence_note: str | None = Field(
        default=None,
        description="Free-text note about extraction confidence or ambiguity.",
    )
