'use client';

import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import {
  Sliders, Play, Trash2, ArrowUp, ArrowDown, Minus,
  TrendingUp, Sparkles, RotateCcw, Plus, Activity,
} from 'lucide-react';
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell, Legend,
  LineChart, Line, CartesianGrid, ReferenceLine,
} from 'recharts';
import { scenarioApi } from '@/services/api/scenarioApi';
import { Badge } from '@/components/ui/Badge';
import { SkeletonCard } from '@/components/ui/Skeleton';
import { ErrorState } from '@/components/ui/ErrorState';
import { EmptyState } from '@/components/ui/EmptyState';
import type { ScenarioSummary, ScenarioSimulation, ScenarioCreateRequest } from '@/types';
import { getActiveWorkspaceId, useWorkspaceStore } from '@/store/workspaceStore';

const DEFAULT_FORM: ScenarioCreateRequest = {
  project_id: '',
  name: 'Custom Scenario',
  description: null,
  shipping_multiplier: 1.0,
  currency_rate: 1.0,
  demand_multiplier: 1.0,
  lead_time_adjustment_days: 0,
  disabled_supplier_ids: [],
};

function RankArrow({ baseline, scenario }: { baseline: number; scenario: number }) {
  const delta = baseline - scenario;
  if (delta > 0) return (
    <span className="text-[var(--success)] flex items-center gap-0.5 font-bold">
      <ArrowUp className="w-3.5 h-3.5" />+{delta}
    </span>
  );
  if (delta < 0) return (
    <span className="text-[var(--danger)] flex items-center gap-0.5 font-bold">
      <ArrowDown className="w-3.5 h-3.5" />{delta}
    </span>
  );
  return (
    <span className="text-[var(--text-muted)] flex items-center gap-0.5">
      <Minus className="w-3.5 h-3.5" />—
    </span>
  );
}

export default function ScenariosPage() {
  const qc = useQueryClient();
  const [form, setForm] = useState<ScenarioCreateRequest>(DEFAULT_FORM);
  const [simResult, setSimResult] = useState<ScenarioSimulation | null>(null);
  const [runningId, setRunningId] = useState<string | null>(null);
  const [builderOpen, setBuilderOpen] = useState(false); // mobile accordion

  const activeWorkspaceId = useWorkspaceStore(state => state.activeWorkspaceId);
  const currentProjectId = activeWorkspaceId || getActiveWorkspaceId();

  const { data: scenarios = [], isLoading, isError, refetch } = useQuery({
    queryKey: ['scenarios', currentProjectId],
    queryFn: () => scenarioApi.list(currentProjectId),
  });

  const createMutation = useMutation({
    mutationFn: (payload: ScenarioCreateRequest) => scenarioApi.create(payload),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['scenarios'] }); toast.success('Scenario created'); },
    onError: () => toast.error('Failed to create scenario'),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => scenarioApi.delete(id),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['scenarios'] }); toast.success('Scenario deleted'); },
  });

  const simulateMutation = useMutation({
    mutationFn: (id: string) => scenarioApi.simulate(id),
    onSuccess: (result) => { setSimResult(result); toast.success('Simulation complete'); },
    onError: () => toast.error('Simulation failed'),
  });

  async function handleSimulate(id: string) {
    setRunningId(id);
    setSimResult(null);
    await simulateMutation.mutateAsync(id);
    setRunningId(null);
  }

  async function handleCreate() {
    await createMutation.mutateAsync({ ...form, project_id: currentProjectId });
    setForm(DEFAULT_FORM);
    setBuilderOpen(false);
  }

  const chartData = simResult?.rankings.map(r => ({
    name: r.supplier_name.split(' ')[0],
    baseline: r.baseline_score,
    scenario: r.scenario_score,
    changed: r.rank_changed,
  })) ?? [];

  const sensitivityData = React.useMemo(() => {
    if (!simResult) return [];
    const steps = [0.5, 0.75, 1.0, 1.25, 1.4, 1.5, 1.75, 2.0, 2.25, 2.5];
    return steps.map(mult => {
      const point: Record<string, number | string> = { shipping: `×${mult.toFixed(2)}` };
      simResult.rankings.forEach(r => {
        const delta = r.scenario_score - r.baseline_score;
        const frac = (mult - 1.0) / (simResult.scenario_shipping_multiplier !== undefined
          ? (simResult.scenario_shipping_multiplier - 1.0) || 1 : 1);
        point[r.supplier_name.split(' ')[0]] = +(r.baseline_score + delta * frac).toFixed(1);
      });
      return point;
    });
  }, [simResult]);

  // ── Shared builder form content ──────────────────────────────────────────
  const BuilderForm = (
    <div className="space-y-3 text-xs">
      <div>
        <label className="text-[var(--text-secondary)] font-semibold block mb-1">Name</label>
        <input
          value={form.name}
          onChange={e => setForm(f => ({ ...f, name: e.target.value }))}
          className="w-full px-3 py-2 rounded-lg bg-[var(--surface-subtle)] border border-[var(--border)] text-[var(--text-primary)] focus:outline-none focus:border-[var(--brand)] transition-colors"
        />
      </div>

      {([
        { key: 'shipping_multiplier', label: 'Shipping Cost ×', min: 0.5, max: 3, step: 0.1 },
        { key: 'currency_rate',       label: 'Currency Rate ×', min: 0.5, max: 2, step: 0.05 },
        { key: 'demand_multiplier',   label: 'Demand ×',        min: 0.5, max: 2, step: 0.1 },
      ] as const).map(({ key, label, min, max, step }) => {
        const val = form[key as keyof ScenarioCreateRequest] as number;
        const pct = ((val - 1) * 100).toFixed(0);
        return (
          <div key={key}>
            <div className="flex justify-between mb-1">
              <label className="text-[var(--text-secondary)] font-semibold">{label}</label>
              <span className="font-bold text-[var(--brand)] num-tabular">
                {val.toFixed(2)}× {val !== 1 && `(${val > 1 ? '+' : ''}${pct}%)`}
              </span>
            </div>
            <input
              type="range" min={min} max={max} step={step} value={val}
              onChange={e => setForm(f => ({ ...f, [key]: parseFloat(e.target.value) }))}
              className="w-full h-1.5 rounded-lg bg-[var(--surface-subtle)] accent-[var(--brand)] cursor-pointer"
            />
          </div>
        );
      })}

      <div>
        <div className="flex justify-between mb-1">
          <label className="text-[var(--text-secondary)] font-semibold">Lead Time Adjustment</label>
          <span className="font-bold text-[var(--brand)] num-tabular">
            {form.lead_time_adjustment_days > 0 ? '+' : ''}{form.lead_time_adjustment_days}d
          </span>
        </div>
        <input
          type="range" min={-10} max={20} step={1}
          value={form.lead_time_adjustment_days}
          onChange={e => setForm(f => ({ ...f, lead_time_adjustment_days: parseInt(e.target.value) }))}
          className="w-full h-1.5 rounded-lg bg-[var(--surface-subtle)] accent-[var(--brand)] cursor-pointer"
        />
      </div>

      <div className="flex gap-2 pt-2">
        <button
          onClick={() => setForm(DEFAULT_FORM)}
          className="flex items-center gap-1.5 px-3 py-2 text-xs font-semibold rounded-lg bg-[var(--surface-subtle)] border border-[var(--border)] text-[var(--text-secondary)] hover:bg-[var(--surface-tertiary)] transition-all"
        >
          <RotateCcw className="w-3.5 h-3.5" /> Reset
        </button>
        <button
          onClick={handleCreate}
          disabled={createMutation.isPending}
          className="flex-1 flex items-center justify-center gap-1.5 px-3 py-2 text-xs font-semibold rounded-lg bg-[var(--surface-ink)] text-[var(--surface)] hover:opacity-90 transition-all disabled:opacity-50"
        >
          <Plus className="w-3.5 h-3.5" /> Save Scenario
        </button>
      </div>
    </div>
  );

  return (
    <div className="max-w-6xl mx-auto space-y-4 sm:space-y-6 pb-12">

      {/* ── Page Header ─────────────────────────────────────────────── */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-[var(--text-primary)]">Scenario Simulator</h1>
          <p className="text-xs text-[var(--text-secondary)] mt-0.5">
            Model what-if scenarios and see how supplier rankings change
          </p>
        </div>
        {/* Mobile: floating button to open builder accordion */}
        <button
          onClick={() => setBuilderOpen(o => !o)}
          className="lg:hidden flex items-center gap-1.5 px-3 py-2 text-xs font-semibold rounded-lg bg-[var(--surface-ink)] text-[var(--surface)] hover:opacity-90 transition-all"
        >
          <Plus className="w-3.5 h-3.5" />
          {builderOpen ? 'Close' : 'New'}
        </button>
      </div>

      {/* ── Mobile Builder Accordion (lg:hidden) ─────────────────────── */}
      {builderOpen && (
        <div className="lg:hidden bg-[var(--surface)] rounded-xl border border-[var(--border)] p-4 shadow-[var(--shadow-card)] space-y-4">
          <h2 className="text-sm font-bold text-[var(--text-primary)] flex items-center gap-2">
            <Sliders className="w-4 h-4 text-[var(--brand)]" /> New Scenario
          </h2>
          {BuilderForm}
        </div>
      )}

      {/* ── Desktop: 3-col layout ─────────────────────────────────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 sm:gap-6">

        {/* Builder Panel — desktop sidebar (hidden on mobile, shown via accordion above) */}
        <div className="hidden lg:block bg-[var(--surface)] rounded-xl border border-[var(--border)] p-5 shadow-[var(--shadow-card)] space-y-4">
          <h2 className="text-sm font-bold text-[var(--text-primary)] flex items-center gap-2">
            <Sliders className="w-4 h-4 text-[var(--brand)]" /> New Scenario
          </h2>
          {BuilderForm}
        </div>

        {/* ── Saved Scenarios ──────────────────────────────────────────── */}
        <div className="lg:col-span-2 space-y-3 sm:space-y-4">
          <h2 className="text-sm font-bold text-[var(--text-primary)]">Saved Scenarios</h2>
          {isLoading && <SkeletonCard lines={3} />}
          {isError && <ErrorState onRetry={() => refetch()} />}
          {!isLoading && scenarios.length === 0 && (
            <EmptyState
              title="No scenarios yet"
              description="Create one using the builder above."
              icon={Sliders}
            />
          )}
          {scenarios.map((s: ScenarioSummary) => (
            <div key={s.id} className="bg-[var(--surface)] rounded-xl border border-[var(--border)] p-4 shadow-[var(--shadow-card)]">
              <div className="flex items-start justify-between gap-3 mb-3">
                <div className="min-w-0">
                  <div className="text-sm font-bold text-[var(--text-primary)] truncate">{s.name}</div>
                  {s.description && (
                    <div className="text-xs text-[var(--text-muted)] mt-0.5 line-clamp-2">{s.description}</div>
                  )}
                </div>
                <div className="flex items-center gap-2 shrink-0">
                  <button
                    onClick={() => handleSimulate(s.id)}
                    disabled={simulateMutation.isPending && runningId === s.id}
                    className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-lg bg-[var(--brand)] text-white hover:bg-[var(--brand-hover)] transition-all disabled:opacity-60"
                  >
                    {simulateMutation.isPending && runningId === s.id
                      ? <><span className="animate-spin inline-block">⟳</span><span className="hidden sm:inline"> Running…</span></>
                      : <><Play className="w-3 h-3" /><span className="hidden sm:inline"> Simulate</span></>}
                  </button>
                  <button
                    onClick={() => deleteMutation.mutate(s.id)}
                    className="text-[var(--danger)] hover:opacity-70 p-1"
                    aria-label="Delete scenario"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
              <div className="flex flex-wrap gap-2 text-[10px] font-mono">
                {s.shipping_multiplier !== 1 && <Badge variant="warning">Ship ×{s.shipping_multiplier}</Badge>}
                {s.currency_rate !== 1 && <Badge variant="info">FX ×{s.currency_rate}</Badge>}
                {s.demand_multiplier !== 1 && <Badge variant="info">Demand ×{s.demand_multiplier}</Badge>}
                {s.lead_time_adjustment_days !== 0 && (
                  <Badge variant="outline">LT {s.lead_time_adjustment_days > 0 ? '+' : ''}{s.lead_time_adjustment_days}d</Badge>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* ── Simulation Results ───────────────────────────────────────── */}
      {simResult && (
        <div className="space-y-4">

          {/* Ranking change banner */}
          <div className={`rounded-xl p-4 flex items-center gap-3 border ${
            simResult.ranking_changed
              ? 'bg-[var(--warning-subtle)] border-[var(--warning)]/40'
              : 'bg-[var(--success-subtle)] border-[var(--success)]/40'
          }`}>
            <TrendingUp className={`w-5 h-5 shrink-0 ${simResult.ranking_changed ? 'text-[var(--warning)]' : 'text-[var(--success)]'}`} />
            <div className={`text-xs font-semibold ${simResult.ranking_changed ? 'text-[var(--warning)]' : 'text-[var(--success)]'}`}>
              {simResult.ranking_changed
                ? 'Ranking changed — new #1 supplier under this scenario'
                : 'Rankings stable — same #1 supplier under this scenario'}
            </div>
          </div>

          {/* AI explanation */}
          {simResult.explanation && (
            <div className="bg-[var(--surface)] rounded-xl border border-[var(--border)] border-l-4 border-l-[#7C3AED] p-4 sm:p-5 shadow-[var(--shadow-card)]">
              <div className="flex items-center gap-2 mb-2">
                <Sparkles className="w-4 h-4 text-[#7C3AED] shrink-0" />
                <span className="text-xs font-bold text-[var(--text-primary)] uppercase tracking-wide">AI Analysis</span>
              </div>
              <p className="text-xs text-[var(--text-secondary)] leading-relaxed">{simResult.explanation}</p>
            </div>
          )}

          {/* Delta bar chart */}
          <div className="bg-[var(--surface)] rounded-xl border border-[var(--border)] p-4 sm:p-5 shadow-[var(--shadow-card)]">
            <h3 className="text-sm font-bold text-[var(--text-primary)] mb-4">Score Delta — Baseline vs Scenario</h3>
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={chartData} barGap={4} barCategoryGap="25%">
                <XAxis dataKey="name" tick={{ fontSize: 10 }} />
                <YAxis domain={[0, 100]} tick={{ fontSize: 10 }} width={28} />
                <Tooltip contentStyle={{ fontSize: 11 }} />
                <Legend wrapperStyle={{ fontSize: 11 }} />
                <Bar dataKey="baseline" name="Baseline" fill="var(--border-strong)" radius={[3, 3, 0, 0]} />
                <Bar dataKey="scenario" name="Scenario" radius={[3, 3, 0, 0]}>
                  {chartData.map((entry, i) => (
                    <Cell key={i} fill={entry.changed ? 'var(--brand)' : 'var(--text-muted)'} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Delta table — horizontal scroll on mobile */}
          <div className="bg-[var(--surface)] rounded-xl border border-[var(--border)] overflow-hidden shadow-[var(--shadow-card)]">
            <div className="px-4 sm:px-5 py-3 bg-[var(--surface-subtle)] border-b border-[var(--border)] text-xs font-semibold text-[var(--text-secondary)]">
              Ranking Delta
            </div>

            {/* Mobile cards */}
            <div className="sm:hidden divide-y divide-[var(--divider)]">
              {simResult.rankings.map((r) => (
                <div
                  key={r.supplier_id}
                  className={`px-4 py-3 space-y-1.5 text-xs ${r.rank_changed ? 'bg-[var(--warning-subtle)]/30' : ''}`}
                >
                  <div className="flex items-center justify-between">
                    <span className="font-semibold text-[var(--text-primary)]">{r.supplier_name}</span>
                    <RankArrow baseline={r.baseline_rank} scenario={r.scenario_rank} />
                  </div>
                  <div className="flex items-center gap-4 text-[var(--text-secondary)] num-tabular">
                    <span>#{r.baseline_rank} → <strong className="text-[var(--text-primary)]">#{r.scenario_rank}</strong></span>
                    <span className="text-[var(--text-muted)]">·</span>
                    <span>{r.baseline_score.toFixed(1)} → <strong className="text-[var(--text-primary)]">{r.scenario_score.toFixed(1)}</strong></span>
                  </div>
                </div>
              ))}
            </div>

            {/* Desktop table */}
            <div className="hidden sm:block overflow-x-auto">
              <table className="w-full text-xs">
                <thead className="border-b border-[var(--divider)] text-[var(--text-secondary)]">
                  <tr>
                    <th className="py-3 px-4 text-left font-semibold">Supplier</th>
                    <th className="py-3 px-4 text-center font-semibold">Before</th>
                    <th className="py-3 px-4 text-center font-semibold">After</th>
                    <th className="py-3 px-4 text-center font-semibold">Change</th>
                    <th className="py-3 px-4 text-right font-semibold">Baseline</th>
                    <th className="py-3 px-4 text-right font-semibold">Scenario</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[var(--divider)]">
                  {simResult.rankings.map((r) => (
                    <tr
                      key={r.supplier_id}
                      className={`hover:bg-[var(--surface-subtle)]/50 ${r.rank_changed ? 'bg-[var(--warning-subtle)]/30' : ''}`}
                    >
                      <td className="py-3 px-4 font-semibold text-[var(--text-primary)]">{r.supplier_name}</td>
                      <td className="py-3 px-4 text-center num-tabular text-[var(--text-secondary)]">#{r.baseline_rank}</td>
                      <td className="py-3 px-4 text-center num-tabular font-bold text-[var(--text-primary)]">#{r.scenario_rank}</td>
                      <td className="py-3 px-4 text-center">
                        <div className="flex justify-center">
                          <RankArrow baseline={r.baseline_rank} scenario={r.scenario_rank} />
                        </div>
                      </td>
                      <td className="py-3 px-4 text-right num-tabular text-[var(--text-secondary)]">{r.baseline_score.toFixed(1)}</td>
                      <td className="py-3 px-4 text-right num-tabular font-bold text-[var(--text-primary)]">{r.scenario_score.toFixed(1)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Sensitivity line chart */}
          {sensitivityData.length > 0 && (
            <div className="bg-[var(--surface)] rounded-xl border border-[var(--border)] p-4 sm:p-5 shadow-[var(--shadow-card)]">
              <div className="flex items-center gap-2 mb-3">
                <Activity className="w-4 h-4 text-[var(--brand)]" />
                <h3 className="text-sm font-bold text-[var(--text-primary)]">
                  Sensitivity — Score vs Shipping Multiplier
                </h3>
              </div>
              <p className="text-xs text-[var(--text-muted)] mb-4">
                Projected score trajectory as shipping costs change. Crossover points show where rankings flip.
              </p>
              <ResponsiveContainer width="100%" height={220}>
                <LineChart data={sensitivityData} margin={{ top: 4, right: 8, bottom: 4, left: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                  <XAxis dataKey="shipping" tick={{ fontSize: 9 }} />
                  <YAxis domain={[0, 100]} tick={{ fontSize: 9 }} width={28} />
                  <Tooltip contentStyle={{ fontSize: 10 }} />
                  <Legend wrapperStyle={{ fontSize: 10 }} />
                  <ReferenceLine
                    x={`×${(simResult.scenario_shipping_multiplier ?? 1).toFixed(2)}`}
                    stroke="var(--warning)"
                    strokeDasharray="4 3"
                    label={{ value: 'Sim', position: 'top', fontSize: 9, fill: 'var(--warning)' }}
                  />
                  {simResult.rankings.map((r, i) => {
                    const colors = ['var(--brand)', 'var(--success)', 'var(--warning)', 'var(--info)', 'var(--danger)', '#9333EA', '#F97316'];
                    return (
                      <Line
                        key={r.supplier_id}
                        type="monotone"
                        dataKey={r.supplier_name.split(' ')[0]}
                        stroke={colors[i % colors.length]}
                        strokeWidth={r.rank_changed ? 2.5 : 1.5}
                        dot={false}
                        activeDot={{ r: 3 }}
                      />
                    );
                  })}
                </LineChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
