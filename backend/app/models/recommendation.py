"""
Manufacturing Decision Copilot - Recommendation Domain Models
"""
from sqlalchemy import Float, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class Recommendation(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "recommendations"

    recommended_supplier_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("suppliers.id", ondelete="CASCADE"), nullable=False
    )
    project_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )

    summary: Mapped[str] = mapped_column(Text, nullable=False)
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False) # Calculated by ConfidenceEngine (0-100)
    confidence_explanation: Mapped[str] = mapped_column(Text, nullable=False)

    pros: Mapped[dict] = mapped_column(JSONB, default=list, nullable=False) # list of strings
    cons: Mapped[dict] = mapped_column(JSONB, default=list, nullable=False)
    tradeoffs: Mapped[dict] = mapped_column(JSONB, default=list, nullable=False)
    risks: Mapped[dict] = mapped_column(JSONB, default=list, nullable=False)
    assumptions: Mapped[dict] = mapped_column(JSONB, default=list, nullable=False)
    next_actions: Mapped[dict] = mapped_column(JSONB, default=list, nullable=False)

    # Relationships
    recommended_supplier: Mapped["Supplier"] = relationship("Supplier")
    evidence_items: Mapped[list["RecommendationEvidence"]] = relationship("RecommendationEvidence", back_populates="recommendation", cascade="all, delete-orphan")


class RecommendationEvidence(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "recommendation_evidence"

    recommendation_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("recommendations.id", ondelete="CASCADE"), nullable=False
    )
    chunk_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("document_chunks.id", ondelete="CASCADE"), nullable=False
    )
    relevance_score: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    snippet: Mapped[str] = mapped_column(Text, nullable=False)

    recommendation: Mapped["Recommendation"] = relationship("Recommendation", back_populates="evidence_items")
    chunk: Mapped["DocumentChunk"] = relationship("DocumentChunk")


class DecisionTrace(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "decision_traces"

    project_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    step_name: Mapped[str] = mapped_column(String(100), nullable=False)
    inputs: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    outputs: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    execution_time_ms: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
