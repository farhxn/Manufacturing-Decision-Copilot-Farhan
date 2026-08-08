"""Scenario business service."""

import asyncio

from app.core.logging import get_logger
from app.engines.scenario import simulate_scenario
from app.engines.types import ScenarioConfig
from app.models.scenario import Scenario, ScenarioResult
from app.repositories.project_repository import ProjectRepository
from app.repositories.scenario_repository import ScenarioRepository
from app.repositories.supplier_repository import SupplierRepository
from app.schemas.scenario import (
    ScenarioCreateRequest,
    ScenarioRankingDeltaSchema,
    ScenarioSimulationSchema,
    ScenarioSummarySchema,
)
from app.schemas.supplier import SupplierScoreSchema
from app.services.supplier_mapper import (
    DEFAULT_REQUIRED_CAPABILITIES,
    DEFAULT_REQUIRED_CERTS,
    project_to_weights,
    suppliers_to_inputs,
)

logger = get_logger(__name__)


class ScenarioService:
    def __init__(
        self,
        scenario_repo: ScenarioRepository,
        supplier_repo: SupplierRepository,
        project_repo: ProjectRepository,
    ):
        self.scenario_repo = scenario_repo
        self.supplier_repo = supplier_repo
        self.project_repo = project_repo

    def _to_summary(self, scenario: Scenario) -> ScenarioSummarySchema:
        disabled = scenario.disabled_supplier_ids or []
        if isinstance(disabled, dict):
            disabled = list(disabled.keys())
        return ScenarioSummarySchema(
            id=scenario.id,
            project_id=scenario.project_id,
            name=scenario.name,
            description=scenario.description,
            shipping_multiplier=scenario.shipping_multiplier,
            currency_rate=scenario.currency_rate,
            demand_multiplier=scenario.demand_multiplier,
            lead_time_adjustment_days=scenario.lead_time_adjustment_days,
            disabled_supplier_ids=list(disabled),
        )

    def _scenario_config(self, scenario: Scenario) -> ScenarioConfig:
        disabled = scenario.disabled_supplier_ids or []
        if isinstance(disabled, list):
            availability = {supplier_id: False for supplier_id in disabled}
        else:
            availability = {str(key): not value for key, value in disabled.items()}

        return ScenarioConfig(
            shipping_multiplier=scenario.shipping_multiplier,
            currency_rate=scenario.currency_rate,
            demand_multiplier=scenario.demand_multiplier,
            lead_time_adjustment_days=scenario.lead_time_adjustment_days,
            supplier_availability=availability,
        )

    async def list_scenarios(self, project_id: str) -> list[ScenarioSummarySchema]:
        scenarios = await self.scenario_repo.list_by_project(project_id)
        return [self._to_summary(scenario) for scenario in scenarios]

    async def create_scenario(self, payload: ScenarioCreateRequest) -> ScenarioSummarySchema:
        scenario = Scenario(
            project_id=payload.project_id,
            name=payload.name,
            description=payload.description,
            shipping_multiplier=payload.shipping_multiplier,
            currency_rate=payload.currency_rate,
            demand_multiplier=payload.demand_multiplier,
            lead_time_adjustment_days=payload.lead_time_adjustment_days,
            disabled_supplier_ids=payload.disabled_supplier_ids,
        )
        saved = await self.scenario_repo.create(scenario)
        return self._to_summary(saved)

    async def get_scenario(self, scenario_id: str) -> ScenarioSummarySchema | None:
        scenario = await self.scenario_repo.get_by_id(scenario_id)
        if not scenario:
            return None
        return self._to_summary(scenario)

    async def simulate(self, scenario_id: str) -> ScenarioSimulationSchema | None:
        scenario = await self.scenario_repo.get_by_id(scenario_id)
        if not scenario:
            return None

        project = await self.project_repo.get_by_id(scenario.project_id)
        if not project:
            return None

        suppliers = await self.supplier_repo.list_by_project(scenario.project_id, limit=500)
        supplier_map = {supplier.id: supplier for supplier in suppliers}
        inputs = suppliers_to_inputs(suppliers)
        weights = project_to_weights(project)
        config = self._scenario_config(scenario)

        result = simulate_scenario(
            suppliers=inputs,
            scenario_config=config,
            weights=weights,
            required_certs=list(DEFAULT_REQUIRED_CERTS),
            required_capabilities=list(DEFAULT_REQUIRED_CAPABILITIES),
        )

        baseline_by_id = {item.supplier_id: item for item in result.baseline_ranking}
        scenario_by_id = {item.supplier_id: item for item in result.scenario_ranking}

        persisted_results: list[ScenarioResult] = []
        deltas: list[ScenarioRankingDeltaSchema] = []

        for supplier_id, scenario_item in scenario_by_id.items():
            if scenario_item.disqualified:
                continue
            baseline_item = baseline_by_id.get(supplier_id)
            if not baseline_item:
                continue
            supplier = supplier_map[supplier_id]
            rank_changed = baseline_item.rank != scenario_item.rank
            persisted_results.append(
                ScenarioResult(
                    scenario_id=scenario.id,
                    supplier_id=supplier_id,
                    rank=scenario_item.rank,
                    baseline_rank=baseline_item.rank,
                    overall_score=scenario_item.final_score,
                    landed_cost=scenario_item.landed_cost,
                    rank_changed=rank_changed,
                    explanation=None,
                )
            )
            deltas.append(
                ScenarioRankingDeltaSchema(
                    supplier_id=supplier_id,
                    supplier_name=supplier.name,
                    baseline_rank=baseline_item.rank,
                    scenario_rank=scenario_item.rank,
                    rank_changed=rank_changed,
                    baseline_score=baseline_item.final_score,
                    scenario_score=scenario_item.final_score,
                    landed_cost=scenario_item.landed_cost,
                    scores=SupplierScoreSchema(
                        cost_score=scenario_item.cost_score,
                        quality_score=scenario_item.quality_score,
                        delivery_score=scenario_item.delivery_score,
                        risk_score=scenario_item.risk_score,
                        capability_score=scenario_item.capability_score,
                        compliance_score=scenario_item.compliance_score,
                        final_score=scenario_item.final_score,
                        rank=scenario_item.rank,
                        landed_cost=scenario_item.landed_cost,
                    ),
                )
            )

        deltas.sort(key=lambda item: item.scenario_rank)
        await self.scenario_repo.replace_results(scenario, persisted_results)

        # ── Phase 6: AI explanation (non-blocking fallback) ───────────────────
        ai_explanation: str | None = None
        try:
            ai_explanation = await asyncio.wait_for(
                self._run_explainer_agent(scenario, config, result, deltas, supplier_map),
                timeout=30.0,
            )
        except asyncio.TimeoutError:
            logger.warning("ScenarioExplainerAgent timed out", scenario_id=scenario_id)
        except Exception as exc:
            logger.warning(
                "ScenarioExplainerAgent failed (non-fatal)",
                scenario_id=scenario_id,
                error=str(exc),
            )

        return ScenarioSimulationSchema(
            scenario_id=scenario.id,
            previous_top_supplier_id=result.previous_top_supplier_id,
            new_top_supplier_id=result.new_top_supplier_id,
            ranking_changed=result.ranking_changed,
            rankings=deltas,
            explanation=ai_explanation,
        )

    async def _run_explainer_agent(
        self,
        scenario,
        config,
        result,
        deltas: list[ScenarioRankingDeltaSchema],
        supplier_map: dict,
    ) -> str | None:
        """Run ScenarioExplainerAgent and return the explanation string."""
        from app.ai.client import build_agent, run_agent
        from app.ai.schemas import ScenarioExplanation
        from app.ai.prompts.v1.scenario_explanation import (
            SYSTEM_PROMPT,
            build_user_prompt,
            format_scenario_params,
            format_delta_table,
        )

        prev_name = supplier_map.get(result.previous_top_supplier_id)
        new_name  = supplier_map.get(result.new_top_supplier_id)
        prev_name = prev_name.name if prev_name else result.previous_top_supplier_id
        new_name  = new_name.name  if new_name  else result.new_top_supplier_id

        user_prompt = build_user_prompt(
            scenario_name=scenario.name,
            scenario_params=format_scenario_params(config),
            previous_top=prev_name,
            new_top=new_name,
            ranking_changed=result.ranking_changed,
            delta_table=format_delta_table(deltas),
        )

        agent = build_agent(ScenarioExplanation, SYSTEM_PROMPT)
        output: ScenarioExplanation = await run_agent(agent, user_prompt)
        return output.explanation

    async def delete_scenario(self, scenario_id: str) -> bool:
        scenario = await self.scenario_repo.get_by_id(scenario_id)
        if not scenario:
            return False
        await self.scenario_repo.delete(scenario)
        return True
