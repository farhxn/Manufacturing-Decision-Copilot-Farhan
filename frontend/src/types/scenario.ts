import type { SupplierScore } from './supplier';

export interface ScenarioCreateRequest {
  project_id: string;
  name: string;
  description?: string | null;
  shipping_multiplier: number;
  currency_rate: number;
  demand_multiplier: number;
  lead_time_adjustment_days: number;
  disabled_supplier_ids: string[];
}

export interface ScenarioSummary {
  id: string;
  project_id: string;
  name: string;
  description: string | null;
  shipping_multiplier: number;
  currency_rate: number;
  demand_multiplier: number;
  lead_time_adjustment_days: number;
  disabled_supplier_ids: string[];
}

export interface ScenarioRankingDelta {
  supplier_id: string;
  supplier_name: string;
  baseline_rank: number;
  scenario_rank: number;
  rank_changed: boolean;
  baseline_score: number;
  scenario_score: number;
  landed_cost: number;
  scores: SupplierScore;
}

export interface ScenarioSimulation {
  scenario_id: string;
  previous_top_supplier_id: string;
  new_top_supplier_id: string;
  ranking_changed: boolean;
  rankings: ScenarioRankingDelta[];
  explanation: string | null;
  /** Shipping multiplier that was applied — used by SensitivityChart */
  scenario_shipping_multiplier?: number;
}
