"""
Manufacturing Decision Copilot - Supplier Domain Models
"""
from sqlalchemy import Boolean, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class Supplier(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "suppliers"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    country: Mapped[str] = mapped_column(String(100), nullable=False)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="evaluated", nullable=False)

    # Key Metrics
    overall_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    unit_price: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    landed_cost: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    currency: Mapped[str] = mapped_column(String(10), default="USD", nullable=False)
    lead_time_days: Mapped[int] = mapped_column(Integer, default=14, nullable=False)
    moq: Mapped[int] = mapped_column(Integer, default=100, nullable=False)
    risk_level: Mapped[str] = mapped_column(String(20), default="Low", nullable=False) # Low, Medium, High

    project_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )

    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="suppliers")
    capabilities: Mapped[list["SupplierCapability"]] = relationship("SupplierCapability", back_populates="supplier", cascade="all, delete-orphan")
    certifications: Mapped[list["SupplierCertification"]] = relationship("SupplierCertification", back_populates="supplier", cascade="all, delete-orphan")
    prices: Mapped[list["SupplierPrice"]] = relationship("SupplierPrice", back_populates="supplier", cascade="all, delete-orphan")
    risk_scores: Mapped[list["SupplierRiskScore"]] = relationship("SupplierRiskScore", back_populates="supplier", cascade="all, delete-orphan")


class SupplierCapability(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "supplier_capabilities"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    verified: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    supplier_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("suppliers.id", ondelete="CASCADE"), nullable=False
    )

    supplier: Mapped["Supplier"] = relationship("Supplier", back_populates="capabilities")


class SupplierCertification(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "supplier_certifications"

    name: Mapped[str] = mapped_column(String(255), nullable=False) # e.g. ISO 9001, AS9100D, RoHS
    issuer: Mapped[str | None] = mapped_column(String(255), nullable=True)
    valid_until: Mapped[str | None] = mapped_column(String(50), nullable=True)
    is_valid: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    supplier_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("suppliers.id", ondelete="CASCADE"), nullable=False
    )

    supplier: Mapped["Supplier"] = relationship("Supplier", back_populates="certifications")


class SupplierPrice(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "supplier_prices"

    tier_min_qty: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    unit_price: Mapped[float] = mapped_column(Float, nullable=False)
    currency: Mapped[str] = mapped_column(String(10), default="USD", nullable=False)
    shipping_cost: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    duty_rate: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    supplier_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("suppliers.id", ondelete="CASCADE"), nullable=False
    )

    supplier: Mapped["Supplier"] = relationship("Supplier", back_populates="prices")


class SupplierRiskScore(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "supplier_risk_scores"

    category: Mapped[str] = mapped_column(String(50), nullable=False) # financial, country, supply, compliance, capacity
    score: Mapped[float] = mapped_column(Float, nullable=False) # 0-100 (higher = safer)
    details: Mapped[str | None] = mapped_column(Text, nullable=True)

    supplier_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("suppliers.id", ondelete="CASCADE"), nullable=False
    )

    supplier: Mapped["Supplier"] = relationship("Supplier", back_populates="risk_scores")
