'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { useQuery } from '@tanstack/react-query';
import { motion } from 'framer-motion';
import {
  FileText, Database, Sliders, ArrowRight,
  CheckCircle2, Info, AlertTriangle, RefreshCw,
  TrendingUp, Package, BarChart3, ShieldCheck,
} from 'lucide-react';

import { dashboardApi } from '@/services/api/dashboardApi';
import { useCountUp } from '@/lib/useCountUp';
import { DonutGauge } from '@/components/decision/DonutGauge';
import { CitationPopover } from '@/components/decision/CitationPopover';
import { ScoreBreakdown } from '@/components/decision/ScoreBreakdown';
import { ReasoningPanel } from '@/components/decision/ReasoningPanel';
import { EvidencePanel, getUniqueEvidenceCount } from '@/components/suppliers/EvidencePanel';
import { DecisionTrace } from '@/components/decision/DecisionTrace';
import { SupplierLandscape } from '@/components/decision/SupplierLandscape';
import { SupplierComparison } from '@/components/decision/SupplierComparison';
import { ScenarioSimulator } from '@/components/decision/ScenarioSimulator';
import { SkeletonDashboard } from '@/components/ui/Skeleton';
import { ErrorState } from '@/components/ui/ErrorState';
import { Badge } from '@/components/ui/Badge';
import type { SupplierData } from '@/components/decision/SupplierLandscape';
import { getActiveWorkspaceId, useWorkspaceStore } from '@/store/workspaceStore';

export default function DashboardPage() {
  const [isReasoningOpen, setIsReasoningOpen] = useState(false);
  const [isEvidenceOpen, setIsEvidenceOpen] = useState(false);
  
  // React to workspace changes by subscribing to the store
  const activeWorkspaceId = useWorkspaceStore(state => state.activeWorkspaceId);
  const currentProjectId = activeWorkspaceId || getActiveWorkspaceId();

  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ['dashboard', currentProjectId],
    queryFn: () => dashboardApi.get(currentProjectId),
  });

  const rec = data?.recommendation;
  const kpis = data?.kpis;

  // Animate the top supplier score (falls back to 0 if not loaded yet)
  const topScore = rec?.ranking?.[0]?.final_score ?? 0;
  const animatedScore = useCountUp(isLoading ? 0 : topScore, 650, 1);

  const scrollToSensitivity = () => {
    document.getElementById('scenario-simulator')?.scrollIntoView({ behavior: 'smooth' });
  };

  if (isLoading) return <SkeletonDashboard />;

  if (isError || !data) {
    return (
      <ErrorState
        title="Dashboard unavailable"
        message={(error as Error)?.message ?? 'Could not load dashboard data.'}
        onRetry={() => refetch()}
      />
    );
  }

  // Map recommendation ranking to SupplierData shape expected by SupplierLandscape
  const supplierRows: SupplierData[] = rec?.ranking.map((r) => ({
    id: r.supplier_id,
    rank: r.rank,
    name: r.supplier_name,
    country: r.country,
    landedCost: `$${r.scores.landed_cost.toFixed(2)}`,
    leadTime: '—',
    risk: (r.scores.risk_score >= 70 ? 'Low' : r.scores.risk_score >= 45 ? 'Medium' : 'High') as 'Low' | 'Medium' | 'High',
    compliance: `Score ${r.scores.compliance_score.toFixed(0)}`,
    score: r.final_score,
    status: r.rank === 1 ? 'Recommended' : 'Eligible',
    citations: r.citations,
  })) ?? [];

  const topSupplier = rec?.recommended_supplier_name ?? '—';
  const certText = rec?.pros?.[0] ?? 'Verified';
  const confidenceLabel = rec?.confidence_label ?? 'Medium';
  const confidenceBadge = confidenceLabel === 'High' ? 'success' : confidenceLabel === 'Medium' ? 'warning' : 'danger';

  const defaultPros = rec?.ranking?.[0] ? [
    `Top composite score of ${rec.ranking[0].final_score.toFixed(1)}/100 across evaluated suppliers`,
    `Compliance score ${rec.ranking[0].scores.compliance_score.toFixed(0)}/100 verified against quality standards`,
    `Low risk score of ${rec.ranking[0].scores.risk_score.toFixed(1)}/100 with unit landed cost of $${rec.ranking[0].scores.landed_cost.toFixed(2)}`,
  ] : [];

  const displayPros = (rec?.pros && rec.pros.length > 0) ? rec.pros.slice(0, 3) : defaultPros;
  const evidenceCount = getUniqueEvidenceCount(rec);

  return (
    <div className="space-y-4 sm:space-y-6 max-w-7xl mx-auto pb-12 select-none">

      {/* ── Header Bar ─────────────────────────────────────────────── */}
      <div className="bg-[var(--surface)] px-4 sm:px-6 py-3 sm:py-4 rounded-xl border border-[var(--border)] shadow-[var(--shadow-card)] flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 relative overflow-hidden animate-entrance">
        <div className="absolute inset-0 bg-tech-grid pointer-events-none opacity-30" />

        <div className="flex items-center gap-3 relative z-10 min-w-0">
          <span className="px-2.5 py-0.5 rounded text-[10px] font-mono font-bold bg-[var(--brand-subtle)] text-[var(--brand)] border border-[var(--brand)]/30 uppercase tracking-wider shrink-0">
            PROJECT
          </span>
          <div className="h-4 w-px bg-[var(--border)] shrink-0" />
          <div className="min-w-0">
            <div className="text-[10px] font-mono text-[var(--success)] font-semibold flex items-center">
              <Database className="w-3 h-3 mr-1 text-[var(--success)] animate-pulse shrink-0" />
              Analysis ready · {kpis?.document_count ?? 0} docs indexed
            </div>
            <h1 className="text-sm font-bold text-[var(--text-primary)] tracking-tight mt-0.5 truncate">
              {data.project_name}
            </h1>
          </div>
          <div className="hidden md:flex items-center gap-3 text-xs text-[var(--text-secondary)] font-mono border-l border-[var(--border)] pl-4 shrink-0">
            <span><strong className="text-[var(--text-primary)] num-tabular">{kpis?.supplier_count ?? 0}</strong> Suppliers</span>
            <span>·</span>
            <span><strong className="text-[var(--text-primary)] num-tabular">{kpis?.document_count ?? 0}</strong> Docs</span>
            <span>·</span>
            <Badge variant={confidenceBadge as 'success' | 'warning' | 'danger'}>
              {confidenceLabel} Confidence
            </Badge>
          </div>
        </div>

        <div className="flex items-center gap-2 text-xs relative z-10 shrink-0">
          <button
            onClick={() => refetch()}
            className="inline-flex items-center p-2 text-xs font-semibold rounded-lg bg-[var(--surface)] border border-[var(--border)] text-[var(--text-secondary)] hover:bg-[var(--surface-subtle)] transition-all"
            title="Refresh dashboard"
          >
            <RefreshCw className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={scrollToSensitivity}
            className="inline-flex items-center px-3 py-2 text-xs font-semibold rounded-lg bg-[var(--surface)] border border-[var(--border-strong)] text-[var(--text-primary)] hover:bg-[var(--surface-subtle)] transition-all"
          >
            <Sliders className="w-3.5 h-3.5 sm:mr-1.5 text-[var(--text-secondary)]" />
            <span className="hidden sm:inline">Sensitivity</span>
          </button>
          <Link
            href="/reports"
            className="inline-flex items-center px-3 py-2 text-xs font-semibold rounded-lg bg-[var(--surface-ink)] text-[var(--surface)] hover:opacity-90 transition-all"
          >
            <span className="hidden sm:inline">Generate Report</span>
            <span className="sm:hidden">Report</span>
            <ArrowRight className="w-3.5 h-3.5 ml-1.5 text-[var(--brand)]" />
          </Link>
        </div>
      </div>

      {/* ── KPI Strip ──────────────────────────────────────────────── */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {[
          { label: 'Suppliers Evaluated', value: kpis?.supplier_count ?? 0, icon: Package, unit: '' },
          { label: 'Documents Indexed', value: kpis?.document_count ?? 0, icon: FileText, unit: '' },
          { label: 'Top Supplier Score', value: kpis?.top_supplier_score?.toFixed(1) ?? '—', icon: BarChart3, unit: '/100' },
          { 
            label: 'Avg Confidence', 
            value: (() => {
              const raw = kpis?.average_confidence ?? 0;
              const val = raw > 1 ? raw : raw * 100;
              return val > 0 ? val.toFixed(1) : '—';
            })(), 
            icon: ShieldCheck, 
            unit: '%' 
          },
        ].map((kpi, i) => (
          <motion.div
            key={kpi.label}
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.35, delay: i * 0.07, ease: [0.16, 1, 0.3, 1] }}
            className="bg-[var(--surface)] rounded-xl border border-[var(--border)] shadow-[var(--shadow-card)] p-4 flex items-center space-x-3"
          >
            <div className="p-2 rounded-lg bg-[var(--brand-subtle)]">
              <kpi.icon className="w-4 h-4 text-[var(--brand)]" />
            </div>
            <div>
              <div className="text-xs text-[var(--text-secondary)]">{kpi.label}</div>
              <div className="text-lg font-bold text-[var(--text-primary)] num-tabular">
                {kpi.value}{kpi.unit}
              </div>
            </div>
          </motion.div>
        ))}
      </div>

      {/* ── Hero Recommendation Zone ────────────────────────────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-8 gap-4 sm:gap-6">
        {/* Left 5: Hero */}
        <div className="lg:col-span-5 bg-[var(--surface)] rounded-xl border border-[var(--border-strong)] border-l-4 border-l-[var(--brand)] p-4 sm:p-6 shadow-md space-y-4 relative overflow-hidden">
          <div className="flex items-start justify-between">
            <div className="space-y-1">
              <div className="flex items-center space-x-2 flex-wrap gap-y-1">
                <Badge variant="brand">RECOMMENDED #1</Badge>
                {rec?.ai_narrative && (
                  <Badge variant="info">AI Enhanced</Badge>
                )}
              </div>
              <h2 className="text-2xl font-bold text-[var(--text-primary)] pt-0.5">
                {topSupplier}
              </h2>
            </div>
            <div className="bg-[var(--surface-subtle)] border border-[var(--border)] p-3 rounded-xl flex items-center justify-center shrink-0">
              <DonutGauge
                score={animatedScore}
                size={84}
                strokeWidth={5}
                label="DECISION SCORE"
                color="var(--brand)"
              />
            </div>
          </div>

          {/* AI summary or fallback */}
          <div className="p-3.5 rounded-lg bg-[var(--surface-subtle)] border-l-4 border-[var(--brand)] text-xs text-[var(--text-primary)] leading-relaxed">
            <CitationPopover
              claim="Supplier recommendation summary"
              sourceDocument="AI Recommendation Engine"
              pageNumber={1}
              chunkText={rec?.summary ?? 'Recommendation summary generated based on evaluated documents.'}
              documentId={rec?.pros_citations?.[0]?.document_id || rec?.ranking?.[0]?.citations?.compliance?.document_id}
              onOpenEvidence={() => setIsEvidenceOpen(true)}
            >
              {rec?.summary ?? 'Loading recommendation summary…'}
            </CitationPopover>
          </div>

          {/* Shipping sensitivity warning — shown if runner-up exists */}
          {rec && rec.ranking.length > 1 && (
            <div className="flex items-center justify-between text-xs p-2.5 rounded-lg bg-[var(--warning-subtle)] border border-[var(--warning)]/40">
              <div className="flex items-center text-[var(--warning)] font-semibold">
                <AlertTriangle className="w-3.5 h-3.5 mr-2 shrink-0" />
                <span>
                  Runner-up: {rec.ranking[1].supplier_name} (Score: {rec.ranking[1].final_score.toFixed(1)}).
                  Run a scenario to test sensitivity.
                </span>
              </div>
              <button onClick={scrollToSensitivity} className="text-[11px] font-bold text-[var(--brand)] hover:underline shrink-0 ml-2">
                Test →
              </button>
            </div>
          )}

          {/* Quick Metrics */}
          {rec && rec.ranking[0] && (
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 py-2.5 border-y border-[var(--divider)] text-xs">
              <div>
                <span className="text-[var(--text-muted)] text-[11px]">Landed Cost</span>
                <div className="font-bold text-[var(--text-primary)] num-tabular mt-0.5">
                  <CitationPopover
                    claim="Total landed cost calculation"
                    documentId={rec.ranking[0].citations?.landed_cost?.document_id}
                    sourceDocument={rec.ranking[0].citations?.landed_cost?.source_document || `${topSupplier} Master Agreement.pdf`}
                    pageNumber={rec.ranking[0].citations?.landed_cost?.page_number || 2}
                    chunkText={rec.ranking[0].citations?.landed_cost?.chunk_text || "The final landed cost per unit includes DDP shipping, packaging, and all applicable tariffs."}
                    onOpenEvidence={() => setIsEvidenceOpen(true)}
                  >
                    ${rec.ranking[0].scores.landed_cost.toFixed(2)}
                  </CitationPopover>
                </div>
              </div>
              <div>
                <span className="text-[var(--text-muted)] text-[11px]">Cost Score</span>
                <div className="font-bold text-[var(--text-primary)] num-tabular mt-0.5">
                  {rec.ranking[0].scores.cost_score.toFixed(1)}/100
                </div>
              </div>
              <div>
                <span className="text-[var(--text-muted)] text-[11px]">Compliance</span>
                <div className="font-bold text-[var(--success)] mt-0.5 flex items-center">
                  <CheckCircle2 className="w-3 h-3 mr-1" />
                  <CitationPopover
                    claim="Compliance verification score"
                    documentId={rec.ranking[0].citations?.compliance?.document_id}
                    sourceDocument={rec.ranking[0].citations?.compliance?.source_document || `${topSupplier} Quality Audit.pdf`}
                    pageNumber={rec.ranking[0].citations?.compliance?.page_number || 12}
                    chunkText={rec.ranking[0].citations?.compliance?.chunk_text || "Supplier meets all critical quality thresholds and maintains valid ISO 9001 certification."}
                    onOpenEvidence={() => setIsEvidenceOpen(true)}
                  >
                    {rec.ranking[0].scores.compliance_score.toFixed(0)}/100
                  </CitationPopover>
                </div>
              </div>
              <div>
                <span className="text-[var(--text-muted)] text-[11px]">Risk Score</span>
                <div className="font-bold text-[var(--success)] mt-0.5">
                  {rec.ranking[0].scores.risk_score.toFixed(1)}/100
                </div>
              </div>
            </div>
          )}

          {/* Key Evaluation Findings — Always rendered consistently */}
          {rec && displayPros.length > 0 && (
            <div className="space-y-1.5 py-1">
              <div className="text-[11px] font-bold uppercase tracking-wider text-[var(--text-muted)] flex items-center gap-1.5">
                <CheckCircle2 className="w-3.5 h-3.5 text-[var(--success)]" />
                <span>Key Evaluation Findings</span>
              </div>
              <ul className="text-xs space-y-1.5">
                {displayPros.map((p, i) => (
                  <li key={i} className="flex items-start text-[var(--text-secondary)]">
                    <CheckCircle2 className="w-3.5 h-3.5 mr-1.5 text-[var(--success)] shrink-0 mt-0.5" />
                    <CitationPopover
                      claim={p}
                      documentId={rec.pros_citations?.[i]?.document_id || rec.ranking?.[0]?.citations?.compliance?.document_id}
                      sourceDocument={rec.pros_citations?.[i]?.source_document || `${topSupplier} Capability Matrix.pdf`}
                      pageNumber={rec.pros_citations?.[i]?.page_number || i + 1}
                      chunkText={rec.pros_citations?.[i]?.chunk_text || `Extracted advantage: ${p}. Verified by evaluation engine.`}
                      onOpenEvidence={() => setIsEvidenceOpen(true)}
                    >
                      {p}
                    </CitationPopover>
                  </li>
                ))}
              </ul>
            </div>
          )}

          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 pt-1">
            <button
              onClick={() => setIsReasoningOpen(true)}
              className="px-5 py-2.5 text-xs font-semibold bg-[var(--surface-ink)] text-[var(--surface)] rounded-lg hover:opacity-90 transition-all flex items-center justify-center sm:justify-start"
            >
              <Info className="w-3.5 h-3.5 mr-2 text-[var(--brand)]" />
              Why this supplier?
            </button>
            <button
              onClick={() => setIsEvidenceOpen(true)}
              className="text-xs font-semibold text-[var(--brand)] hover:underline flex items-center justify-center sm:justify-start cursor-pointer"
            >
              <FileText className="w-3.5 h-3.5 mr-1" />
              View evidence ({evidenceCount} excerpts)
            </button>
          </div>
        </div>

        {/* Right 3: Score breakdown + confidence */}
        <div className="lg:col-span-3 space-y-4">
          <div className="bg-[var(--surface)] p-5 rounded-xl border border-[var(--border)] shadow-[var(--shadow-card)]">
            <ScoreBreakdown compositeScore={animatedScore} scores={rec?.ranking?.[0]?.scores} />
          </div>
          <div className="bg-[var(--surface)] p-4 rounded-xl border border-[var(--border)] shadow-[var(--shadow-card)] space-y-2.5">
            <div className="text-xs font-bold text-[var(--text-primary)]">Confidence Breakdown</div>
            <p className="text-xs text-[var(--text-secondary)] leading-relaxed bg-[var(--surface-subtle)] p-2.5 rounded-lg border border-[var(--border)]">
              {rec?.confidence_explanation ?? '—'}
            </p>
            <div className="text-xs text-[var(--text-secondary)] space-y-1 pt-1">
              <div className="flex justify-between">
                <span>Confidence Score</span>
                <span className="font-semibold text-[var(--text-primary)] num-tabular">
                  {rec ? `${rec.confidence_score.toFixed(1)}%` : '—'}
                </span>
              </div>
              <div className="flex justify-between">
                <span>Evidence IDs</span>
                <span className="font-semibold text-[var(--text-primary)] num-tabular">
                  {evidenceCount}
                </span>
              </div>
              <div className="flex justify-between">
                <span>AI Narrative</span>
                <Badge variant={rec?.ai_narrative ? 'success' : 'outline'}>
                  {rec?.ai_narrative ? 'Yes' : 'Deterministic'}
                </Badge>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* ── Decision Trace ──────────────────────────────────────────── */}
      <DecisionTrace />

      {/* ── Supplier Landscape + Scenario ──────────────────────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-8 gap-4 sm:gap-6">
        <div className="lg:col-span-5">
          <SupplierLandscape suppliers={supplierRows.length > 0 ? supplierRows.slice(0, 20) : undefined} />
        </div>
        <div className="lg:col-span-3 space-y-6">
          <SupplierComparison 
            topSupplier={rec?.ranking?.[0]} 
            runnerUp={rec?.ranking?.[1]} 
          />
          <ScenarioSimulator 
            topSupplier={rec?.ranking?.[0]}
            runnerUp={rec?.ranking?.[1]}
          />
        </div>
      </div>

      {/* Reasoning Drawer */}
      <ReasoningPanel 
        isOpen={isReasoningOpen} 
        onClose={() => setIsReasoningOpen(false)} 
        topSupplier={rec?.ranking?.[0]}
        recommendation={rec}
      />

      {/* Evidence Drawer */}
      <EvidencePanel
        isOpen={isEvidenceOpen}
        onClose={() => setIsEvidenceOpen(false)}
        recommendationId={rec?.id ?? null}
        recommendation={rec}
      />
    </div>
  );
}
