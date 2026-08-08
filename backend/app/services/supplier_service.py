"""Supplier business service."""

from __future__ import annotations

import math

from app.engines.ranking import score_suppliers
from app.engines.risk import calculate_risk_breakdown
from app.engines.types import SupplierScoreBreakdown
from app.models.supplier import Supplier
from app.repositories.project_repository import ProjectRepository
from app.repositories.supplier_repository import SupplierRepository
from app.schemas.common import PaginationMeta
from app.schemas.supplier import (
    RiskBreakdownSchema,
    RiskFactorSchema,
    SupplierCapabilitySchema,
    SupplierCertificationSchema,
    SupplierDetailSchema,
    SupplierScoreSchema,
    SupplierSummarySchema,
    SupplierCreateSchema,
    SupplierUpdateSchema,
)
from app.services.supplier_mapper import (
    DEFAULT_REQUIRED_CAPABILITIES,
    DEFAULT_REQUIRED_CERTS,
    project_to_weights,
    supplier_to_risk_meta,
    suppliers_to_inputs,
)


class SupplierService:
    def __init__(
        self,
        supplier_repo: SupplierRepository,
        project_repo: ProjectRepository,
    ):
        self.supplier_repo = supplier_repo
        self.project_repo = project_repo

    # ── Internal helpers ──────────────────────────────────────────────────────

    async def _score_breakdown_map(
        self,
        project_id: str,
        suppliers: list[Supplier],
    ) -> dict[str, SupplierScoreBreakdown]:
        project = await self.project_repo.get_by_id(project_id)
        if not project:
            return {}

        ranking = score_suppliers(
            suppliers=suppliers_to_inputs(suppliers),
            weights=project_to_weights(project),
            required_certs=list(DEFAULT_REQUIRED_CERTS),
            required_capabilities=list(DEFAULT_REQUIRED_CAPABILITIES),
        )
        return {item.supplier_id: item for item in ranking}

    @staticmethod
    def _to_score_schema(breakdown: SupplierScoreBreakdown) -> SupplierScoreSchema:
        return SupplierScoreSchema(
            cost_score=breakdown.cost_score,
            quality_score=breakdown.quality_score,
            delivery_score=breakdown.delivery_score,
            risk_score=breakdown.risk_score,
            capability_score=breakdown.capability_score,
            compliance_score=breakdown.compliance_score,
            final_score=breakdown.final_score,
            rank=breakdown.rank,
            landed_cost=breakdown.landed_cost,
        )

    @staticmethod
    def _to_risk_breakdown_schema(
        supplier: Supplier,
        breakdown: SupplierScoreBreakdown,
    ) -> RiskBreakdownSchema | None:
        """
        Build the fully-auditable RiskBreakdownSchema for the detail endpoint.

        Uses the RiskBreakdown attached to the SupplierScoreBreakdown if available,
        otherwise falls back to recalculating from the supplier's risk_scores rows.
        """
        rb = breakdown.risk_breakdown

        if rb is None:
            # Fallback: recalculate with metadata from DB rows
            meta = supplier_to_risk_meta(supplier)
            risk_row_map = {item.category: item.score for item in supplier.risk_scores}

            def _mag(cat: str) -> float:
                return max(0.0, min(100.0, 100.0 - risk_row_map.get(cat, 70.0)))

            rb = calculate_risk_breakdown(
                financial_risk=_mag("financial"),
                country_risk=_mag("country"),
                supply_risk=_mag("supply"),
                compliance_risk=_mag("compliance"),
                capacity_risk=_mag("capacity"),
                data_sources=meta.data_sources,
                details=meta.details,
                evidence_ids=meta.evidence_ids,
            )

        return RiskBreakdownSchema(
            overall_score=rb.overall_score,
            risk_level=rb.risk_level,
            primary_driver_id=rb.primary_driver_id,
            primary_driver_name=rb.primary_driver_name,
            total_weighted_risk=rb.total_weighted_risk,
            calculation_version=rb.calculation_version,
            evidence_coverage=rb.evidence_coverage,
            factors=[
                RiskFactorSchema(
                    factor_id=f.factor_id,
                    name=f.name,
                    score=f.score,
                    magnitude=f.magnitude,
                    weight=f.weight,
                    weighted_contribution=f.weighted_contribution,
                    data_source=f.data_source,
                    status=f.status,
                    confidence=f.confidence,
                    details=f.details,
                    evidence_ids=list(f.evidence_ids),
                )
                for f in rb.factors
            ],
        )

    def _to_summary(
        self,
        supplier: Supplier,
        breakdown: SupplierScoreBreakdown,
    ) -> SupplierSummarySchema:
        return SupplierSummarySchema(
            id=supplier.id,
            name=supplier.name,
            country=supplier.country,
            city=supplier.city,
            status=supplier.status,
            unit_price=supplier.unit_price,
            landed_cost=breakdown.landed_cost,
            currency=supplier.currency,
            lead_time_days=supplier.lead_time_days,
            moq=supplier.moq,
            risk_level=supplier.risk_level,
            scores=self._to_score_schema(breakdown),
        )

    # ── Public API ────────────────────────────────────────────────────────────

    async def list_suppliers(
        self,
        project_id: str,
        *,
        page: int = 1,
        limit: int = 20,
        search: str | None = None,
        country: str | None = None,
    ) -> tuple[list[SupplierSummarySchema], PaginationMeta]:
        offset = (page - 1) * limit
        suppliers = await self.supplier_repo.list_by_project(
            project_id,
            limit=limit,
            offset=offset,
            search=search,
            country=country,
        )
        total = await self.supplier_repo.count_by_project(
            project_id,
            search=search,
            country=country,
        )
        breakdown_map = await self._score_breakdown_map(project_id, suppliers)

        items = [
            self._to_summary(
                supplier,
                breakdown_map.get(
                    supplier.id,
                    SupplierScoreBreakdown(
                        supplier_id=supplier.id,
                        landed_cost=supplier.landed_cost,
                        cost_score=0.0,
                        quality_score=0.0,
                        delivery_score=0.0,
                        risk_score=0.0,
                        capability_score=0.0,
                        compliance_score=0.0,
                        final_score=0.0,
                    ),
                ),
            )
            for supplier in suppliers
        ]
        items.sort(key=lambda item: item.scores.rank or 999)

        meta = PaginationMeta(
            page=page,
            limit=limit,
            total=total,
            total_pages=max(1, math.ceil(total / limit)) if total else 0,
        )
        return items, meta

    async def get_supplier(self, supplier_id: str) -> SupplierDetailSchema | None:
        supplier = await self.supplier_repo.get_by_id(supplier_id)
        if not supplier:
            return None

        breakdown_map = await self._score_breakdown_map(supplier.project_id, [supplier])
        breakdown = breakdown_map.get(
            supplier.id,
            SupplierScoreBreakdown(
                supplier_id=supplier.id,
                landed_cost=supplier.landed_cost,
                cost_score=0.0,
                quality_score=0.0,
                delivery_score=0.0,
                risk_score=0.0,
                capability_score=0.0,
                compliance_score=0.0,
                final_score=0.0,
            ),
        )
        summary = self._to_summary(supplier, breakdown)
        risk_breakdown = self._to_risk_breakdown_schema(supplier, breakdown)

        return SupplierDetailSchema(
            **summary.model_dump(),
            capabilities=[
                SupplierCapabilitySchema(
                    name=cap.name,
                    category=cap.category,
                    verified=cap.verified,
                )
                for cap in supplier.capabilities
            ],
            certifications=[
                SupplierCertificationSchema(
                    name=cert.name,
                    issuer=cert.issuer,
                    is_valid=cert.is_valid,
                )
                for cert in supplier.certifications
            ],
            risk_breakdown=risk_breakdown,
        )

    async def create_supplier(self, data: SupplierCreateSchema) -> SupplierSummarySchema:
        supplier = Supplier(
            name=data.name,
            country=data.country,
            city=data.city,
            status=data.status,
            unit_price=data.unit_price,
            landed_cost=data.landed_cost,
            currency=data.currency,
            lead_time_days=data.lead_time_days,
            moq=data.moq,
            risk_level=data.risk_level,
            project_id=data.project_id or "00000000-0000-4000-a000-000000000002"
        )
        saved = await self.supplier_repo.create(supplier)
        breakdown_map = await self._score_breakdown_map(saved.project_id, [saved])
        breakdown = breakdown_map.get(
            saved.id,
            SupplierScoreBreakdown(
                supplier_id=saved.id,
                landed_cost=saved.landed_cost,
                cost_score=0.0,
                quality_score=0.0,
                delivery_score=0.0,
                risk_score=0.0,
                capability_score=0.0,
                compliance_score=0.0,
                final_score=0.0,
            ),
        )
        return self._to_summary(saved, breakdown)

    async def update_supplier(self, supplier_id: str, data: SupplierUpdateSchema) -> SupplierSummarySchema | None:
        supplier = await self.supplier_repo.get_by_id(supplier_id)
        if not supplier:
            return None
        
        update_data = data.model_dump(exclude_unset=True)
        if update_data:
            supplier = await self.supplier_repo.update(supplier, update_data)
        
        breakdown_map = await self._score_breakdown_map(supplier.project_id, [supplier])
        breakdown = breakdown_map.get(
            supplier.id,
            SupplierScoreBreakdown(
                supplier_id=supplier.id,
                landed_cost=supplier.landed_cost,
                cost_score=0.0,
                quality_score=0.0,
                delivery_score=0.0,
                risk_score=0.0,
                capability_score=0.0,
                compliance_score=0.0,
                final_score=0.0,
            ),
        )
        return self._to_summary(supplier, breakdown)

    async def delete_supplier(self, supplier_id: str) -> bool:
        supplier = await self.supplier_repo.get_by_id(supplier_id)
        if not supplier:
            return False
        await self.supplier_repo.delete(supplier)
        return True

