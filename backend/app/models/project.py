"""
Manufacturing Decision Copilot - Project Model
"""
from sqlalchemy import Float, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class Project(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "projects"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="active", nullable=False)

    organization_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )

    # Configurable Scoring Weights
    cost_weight: Mapped[float] = mapped_column(Float, default=0.30, nullable=False)
    quality_weight: Mapped[float] = mapped_column(Float, default=0.20, nullable=False)
    delivery_weight: Mapped[float] = mapped_column(Float, default=0.15, nullable=False)
    risk_weight: Mapped[float] = mapped_column(Float, default=0.15, nullable=False)
    capability_weight: Mapped[float] = mapped_column(Float, default=0.10, nullable=False)
    compliance_weight: Mapped[float] = mapped_column(Float, default=0.10, nullable=False)

    # Relationships
    organization: Mapped["Organization"] = relationship("Organization", back_populates="projects")
    suppliers: Mapped[list["Supplier"]] = relationship("Supplier", back_populates="project", cascade="all, delete-orphan")
    documents: Mapped[list["Document"]] = relationship("Document", back_populates="project", cascade="all, delete-orphan")
    scenarios: Mapped[list["Scenario"]] = relationship("Scenario", back_populates="project", cascade="all, delete-orphan")
