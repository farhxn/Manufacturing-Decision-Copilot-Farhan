"""Scenario API routes."""

from fastapi import APIRouter, Depends, Query

from app.core.dependencies import get_scenario_service
from app.core.exceptions import AppHTTPException
from app.schemas.common import APIResponse
from app.schemas.scenario import (
    ScenarioCreateRequest,
    ScenarioSimulationSchema,
    ScenarioSummarySchema,
)
from app.services.scenario_service import ScenarioService

router = APIRouter(prefix="/scenarios", tags=["Scenarios"])

DEFAULT_PROJECT_ID = "00000000-0000-4000-a000-000000000002"


@router.get("", response_model=APIResponse[list[ScenarioSummarySchema]])
async def list_scenarios(
    project_id: str = Query(DEFAULT_PROJECT_ID),
    service: ScenarioService = Depends(get_scenario_service),
):
    scenarios = await service.list_scenarios(project_id)
    return APIResponse(
        success=True,
        message="Scenarios retrieved successfully.",
        data=scenarios,
    )


@router.post("", response_model=APIResponse[ScenarioSummarySchema], status_code=201)
async def create_scenario(
    payload: ScenarioCreateRequest,
    service: ScenarioService = Depends(get_scenario_service),
):
    scenario = await service.create_scenario(payload)
    return APIResponse(
        success=True,
        message="Scenario created successfully.",
        data=scenario,
    )


@router.get("/{scenario_id}", response_model=APIResponse[ScenarioSummarySchema])
async def get_scenario(
    scenario_id: str,
    service: ScenarioService = Depends(get_scenario_service),
):
    scenario = await service.get_scenario(scenario_id)
    if not scenario:
        raise AppHTTPException(
            status_code=404,
            code="SCENARIO_NOT_FOUND",
            message=f"Scenario {scenario_id} was not found.",
        )
    return APIResponse(
        success=True,
        message="Scenario retrieved successfully.",
        data=scenario,
    )


@router.post("/{scenario_id}/simulate", response_model=APIResponse[ScenarioSimulationSchema])
async def simulate_scenario(
    scenario_id: str,
    service: ScenarioService = Depends(get_scenario_service),
):
    result = await service.simulate(scenario_id)
    if not result:
        raise AppHTTPException(
            status_code=404,
            code="SCENARIO_NOT_FOUND",
            message=f"Scenario {scenario_id} was not found.",
        )
    return APIResponse(
        success=True,
        message="Scenario simulated successfully.",
        data=result,
    )


@router.delete("/{scenario_id}", status_code=204)
async def delete_scenario(
    scenario_id: str,
    service: ScenarioService = Depends(get_scenario_service),
):
    deleted = await service.delete_scenario(scenario_id)
    if not deleted:
        raise AppHTTPException(
            status_code=404,
            code="SCENARIO_NOT_FOUND",
            message=f"Scenario {scenario_id} was not found.",
        )
