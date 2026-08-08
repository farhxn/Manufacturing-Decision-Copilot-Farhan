"""
Manufacturing Decision Copilot - Scenario Domain Models
"""
from sqlalchemy import Boolean, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class Scenario(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "scenarios"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    project_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )

    # Scenario Variables
    shipping_multiplier: Mapped[float] = mapped_column(Float, default=1.0, nullable=False) # e.g. 1.4 = +40%
    currency_rate: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    demand_multiplier: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    lead_time_adjustment_days: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    disabled_supplier_ids: Mapped[dict] = mapped_column(JSONB, default=list, nullable=False) # list of supplier UUID strings

    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="scenarios")
    results: Mapped[list["ScenarioResult"]] = relationship("ScenarioResult", back_populates="scenario", cascade="all, delete-orphan")


class ScenarioResult(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "scenario_results"

    scenario_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("scenarios.id", ondelete="CASCADE"), nullable=False
    )
    supplier_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("suppliers.id", ondelete="CASCADE"), nullable=False
    )

    rank: Mapped[int] = mapped_column(Integer, nullable=False)
    baseline_rank: Mapped[int] = mapped_column(Integer, nullable=False)
    overall_score: Mapped[float] = mapped_column(Float, nullable=False)
    landed_cost: Mapped[float] = mapped_column(Float, nullable=False)
    rank_changed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    explanation: Mapped[str | None] = mapped_column(Text, nullable=True)

    scenario: Mapped["Scenario"] = relationship("Scenario", back_populates="results")
    supplier: Mapped["Supplier"] = relationship("Supplier")
