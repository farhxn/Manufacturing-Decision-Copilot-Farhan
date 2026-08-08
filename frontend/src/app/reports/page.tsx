'use client';

import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import {
  FileDown, Sparkles, RefreshCw, CheckCircle2, AlertTriangle,
  TrendingUp, Loader2, History, Trash2, Clock,
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { dashboardApi } from '@/services/api/dashboardApi';
import { recommendationApi } from '@/services/api/recommendationApi';
import { reportApi } from '@/services/api/reportApi';
import { Badge } from '@/components/ui/Badge';
import { SkeletonCard } from '@/components/ui/Skeleton';
import { ErrorState } from '@/components/ui/ErrorState';
import { EmptyState } from '@/components/ui/EmptyState';
import type { ReportPDFData } from '@/components/reports/ReportPDF';
import { getActiveWorkspaceId, useWorkspaceStore } from '@/store/workspaceStore';

// ── Section helpers ───────────────────────────────────────────────────────────

function Section({ title, items }: { title: string; items: string[] }) {
  if (!items.length) return null;
  return (
    <div>
      <h4 className="text-xs font-bold text-[var(--text-primary)] uppercase tracking-wide mb-2">{title}</h4>
      <ul className="space-y-1.5">
        {items.map((item, i) => (
          <li key={i} className="flex items-start gap-2 text-xs text-[var(--text-secondary)]">
            <CheckCircle2 className="w-3.5 h-3.5 text-[var(--success)] shrink-0 mt-0.5" />
            {item}
          </li>
        ))}
      </ul>
    </div>
  );
}

function RiskSection({ items }: { items: string[] }) {
  if (!items.length) return null;
  return (
    <div>
      <h4 className="text-xs font-bold text-[var(--text-primary)] uppercase tracking-wide mb-2">Risks</h4>
      <ul className="space-y-1.5">
        {items.map((item, i) => (
          <li key={i} className="flex items-start gap-2 text-xs text-[var(--text-secondary)]">
            <AlertTriangle className="w-3.5 h-3.5 text-[var(--warning)] shrink-0 mt-0.5" />
            {item}
          </li>
        ))}
      </ul>
    </div>
  );
}

// ── PDF download helper ───────────────────────────────────────────────────────

async function downloadAsPDF(pdfData: ReportPDFData): Promise<void> {
  const { pdf } = await import('@react-pdf/renderer');
  const { ReportPDF } = await import('@/components/reports/ReportPDF');
  const blob = await pdf(<ReportPDF data={pdfData} />).toBlob();
  const url  = URL.createObjectURL(blob);
  const a    = document.createElement('a');
  const safe = pdfData.project_name.replace(/\s+/g, '_').replace(/[^a-zA-Z0-9_-]/g, '');
  a.href     = url;
  a.download = `MDC_Report_${safe}_${Date.now()}.pdf`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

// ── Page ──────────────────────────────────────────────────────────────────────

export default function ReportsPage() {
  const qc = useQueryClient();
  const [regenerating, setRegenerating] = useState(false);
  const [downloading,  setDownloading]  = useState(false);

  const activeWorkspaceId = useWorkspaceStore(state => state.activeWorkspaceId);
  const currentProjectId  = activeWorkspaceId || getActiveWorkspaceId();

  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ['dashboard', currentProjectId],
    queryFn:  () => dashboardApi.get(currentProjectId),
  });

  const { data: historyReports = [], refetch: refetchHistory } = useQuery({
    queryKey: ['reports', currentProjectId],
    queryFn:  () => reportApi.list(currentProjectId, 10),
  });

  const regenMutation = useMutation({
    mutationFn: () => recommendationApi.regenerate(currentProjectId),
    onSuccess: () => {
      toast.success('Report regenerated with latest AI analysis');
      refetch();
      setRegenerating(false);
    },
    onError: () => { toast.error('Regeneration failed'); setRegenerating(false); },
  });

  const deleteReportMutation = useMutation({
    mutationFn: (id: string) => reportApi.delete(id),
    onSuccess: () => { toast.success('Report deleted'); refetchHistory(); },
    onError:   () => toast.error('Delete failed'),
  });

  async function handleDownload() {
    if (!data) return;
    setDownloading(true);
    try {
      const rec = data.recommendation;
      
      // Generate the AI summary on the backend
      const apiResponse = await reportApi.generate({
        project_id:  currentProjectId,
        report_type: 'executive',
        title: `${data.project_name} — Executive Report`,
      });
      
      // Parse the JSON output from the agent
      let aiSummary;
      try {
        aiSummary = JSON.parse(apiResponse.summary_text);
      } catch (e) {
        console.error("Failed to parse AI summary:", apiResponse.summary_text);
        throw new Error("Failed to parse AI summary from backend");
      }

      const pdfData: ReportPDFData = {
        project_name:              data.project_name,
        generated_at:              new Date().toLocaleString('en-GB', { dateStyle: 'medium', timeStyle: 'short' }),
        recommended_supplier_name: rec.recommended_supplier_name,
        confidence_score:          rec.confidence_score,
        confidence_label:          rec.confidence_label,
        confidence_explanation:    rec.confidence_explanation,
        executive_summary:         aiSummary.executive_summary || rec.summary,
        recommendation_statement:  aiSummary.recommendation_statement || "",
        key_findings:              aiSummary.key_findings || [],
        risk_summary:              aiSummary.risk_summary || [],
        next_steps:                aiSummary.next_steps || [],
        disclaimer:                aiSummary.disclaimer || "This analysis is AI-assisted decision support.",
        ranking: rec.ranking.map(r => ({
          rank:           r.rank,
          supplier_name:  r.supplier_name,
          country:        r.country,
          final_score:    r.final_score,
          landed_cost:    r.scores.landed_cost,
          lead_time_days: r.lead_time_days,
        })),
        evidence_count: rec.evidence_ids?.length ?? 0,
        ai_narrative:   rec.ai_narrative,
      };

      refetchHistory();
      await downloadAsPDF(pdfData);
      toast.success('PDF report downloaded');
    } catch (err) {
      console.error('PDF generation failed', err);
      toast.error('PDF generation failed — please try again');
    } finally {
      setDownloading(false);
    }
  }

  // ── Loading / error ───────────────────────────────────────────────────────

  if (isLoading) return (
    <div className="max-w-4xl mx-auto space-y-4 pb-12">
      <SkeletonCard lines={2} />
      <SkeletonCard lines={6} />
    </div>
  );

  if (isError || !data) return (
    <ErrorState title="Report unavailable" onRetry={() => refetch()} />
  );

  const rec = data.recommendation;

  return (
    <div className="max-w-4xl mx-auto space-y-4 sm:space-y-6 pb-12">

      {/* ── Header ── */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <div>
          <h1 className="text-xl font-bold text-[var(--text-primary)]">Executive Report</h1>
          <p className="text-xs text-[var(--text-secondary)] mt-0.5">{data.project_name}</p>
        </div>
        <div className="flex items-center gap-2 flex-wrap">
          <button
            onClick={() => { setRegenerating(true); regenMutation.mutate(); }}
            disabled={regenMutation.isPending || regenerating}
            aria-label="Regenerate report with AI"
            className="flex-1 sm:flex-none inline-flex items-center justify-center gap-1.5 px-3 sm:px-3.5 py-2 text-xs font-semibold rounded-lg bg-[var(--surface)] border border-[var(--border)] text-[var(--text-primary)] hover:bg-[var(--surface-subtle)] transition-all disabled:opacity-50"
          >
            <RefreshCw className={`w-3.5 h-3.5 shrink-0 ${regenMutation.isPending ? 'animate-spin' : ''}`} />
            <span className="hidden sm:inline">Regenerate with AI</span>
            <span className="sm:hidden">Regenerate</span>
          </button>
          <button
            onClick={handleDownload}
            disabled={downloading}
            aria-label="Download PDF report"
            className="flex-1 sm:flex-none inline-flex items-center justify-center gap-1.5 px-3 sm:px-3.5 py-2 text-xs font-semibold rounded-lg bg-[var(--surface-ink)] text-[var(--surface)] hover:opacity-90 transition-all disabled:opacity-60"
          >
            {downloading
              ? <><Loader2 className="w-3.5 h-3.5 animate-spin shrink-0" /><span>Generating…</span></>
              : <><FileDown className="w-3.5 h-3.5 shrink-0" /><span>Download PDF</span></>}
          </button>
        </div>
      </div>

      {/* ── KPI strip ── */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        {[
          { label: 'Suppliers',      value: data.kpis.supplier_count },
          { label: 'Documents',      value: data.kpis.document_count },
          { label: 'Top Score',      value: `${data.kpis.top_supplier_score.toFixed(1)}/100` },
          { label: 'Avg Confidence', value: `${(data.kpis.average_confidence * 100).toFixed(0)}%` },
        ].map((k, i) => (
          <motion.div
            key={k.label}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3, delay: i * 0.06 }}
            className="bg-[var(--surface)] rounded-xl border border-[var(--border)] p-3 text-center shadow-[var(--shadow-card)]"
          >
            <div className="text-lg font-bold text-[var(--text-primary)] num-tabular">{k.value}</div>
            <div className="text-[11px] text-[var(--text-muted)]">{k.label}</div>
          </motion.div>
        ))}
      </div>

      {/* ── Recommendation hero ── */}
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.38, delay: 0.1, ease: [0.16, 1, 0.3, 1] }}
        className="bg-[var(--surface)] rounded-xl border border-[var(--border-strong)] border-l-4 border-l-[var(--brand)] p-4 sm:p-6 shadow-md space-y-5"
      >
        {/* Hero header — stacks on mobile */}
        <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-3">
          <div className="space-y-1">
            <Badge variant="brand">RECOMMENDED SUPPLIER</Badge>
            <h2 className="text-xl sm:text-2xl font-bold text-[var(--text-primary)] mt-1">
              {rec.recommended_supplier_name}
            </h2>
          </div>
          <div className="flex sm:flex-col sm:text-right items-center sm:items-end gap-3 sm:gap-1 shrink-0">
            <div>
              <div className="text-[10px] text-[var(--text-muted)] uppercase font-mono">Score</div>
              <div className="text-3xl font-extrabold text-[var(--brand)] num-tabular leading-none">
                {rec.ranking[0]?.final_score.toFixed(1) ?? '—'}
              </div>
            </div>
            <Badge variant={
              rec.confidence_label === 'High' ? 'success' :
              rec.confidence_label === 'Medium' ? 'warning' : 'danger'
            }>
              {rec.confidence_label} Confidence
            </Badge>
          </div>
        </div>

        <p className="text-xs text-[var(--text-secondary)] leading-relaxed bg-[var(--surface-subtle)] p-3 rounded-lg border border-[var(--border)]">
          {rec.summary}
        </p>

        {rec.ai_narrative && (
          <div className="flex items-center gap-2 text-xs text-[#7C3AED] bg-purple-50 dark:bg-purple-950/20 px-3 py-2 rounded-lg border border-purple-200 dark:border-purple-900/40">
            <Sparkles className="w-3.5 h-3.5 shrink-0" />
            This report includes AI-generated narrative analysis
          </div>
        )}

        {/* Findings grid — 1-col on xs, 2-col on sm+ */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 sm:gap-6">
          <Section title="Strengths"    items={rec.pros} />
          <Section title="Concerns"     items={rec.cons} />
          <Section title="Tradeoffs"    items={rec.tradeoffs} />
          <RiskSection                  items={rec.risks} />
          <Section title="Assumptions"  items={rec.assumptions} />
          <Section title="Next Actions" items={rec.next_actions} />
        </div>
      </motion.div>

      {/* ── Supplier ranking table ── */}
      <div className="bg-[var(--surface)] rounded-xl border border-[var(--border)] overflow-hidden shadow-[var(--shadow-card)]">
        <div className="px-4 sm:px-5 py-4 border-b border-[var(--border)] flex items-center gap-2">
          <TrendingUp className="w-4 h-4 text-[var(--brand)]" />
          <h3 className="text-sm font-bold text-[var(--text-primary)]">Full Supplier Ranking</h3>
        </div>

        {/* Mobile cards */}
        <div className="sm:hidden divide-y divide-[var(--divider)]">
          {rec.ranking.map((r) => (
            <div
              key={r.supplier_id}
              className={`px-4 py-3 flex items-center justify-between gap-3 text-xs ${r.rank === 1 ? 'bg-[var(--brand-subtle)]/20' : ''}`}
            >
              <div className="min-w-0">
                <div className="flex items-center gap-1.5">
                  <span className="font-mono text-[var(--text-muted)]">#{r.rank}</span>
                  {r.rank === 1 && <span className="w-2 h-2 rounded-full bg-[var(--brand)] shrink-0" />}
                  <span className="font-semibold text-[var(--text-primary)] truncate">{r.supplier_name}</span>
                </div>
                <div className="text-[var(--text-muted)] mt-0.5">{r.country}</div>
              </div>
              <div className="text-right shrink-0">
                <div className="font-bold num-tabular text-[var(--brand)]">{r.final_score.toFixed(1)}</div>
                <div className="text-[var(--text-muted)] num-tabular">${r.scores.landed_cost.toFixed(2)}</div>
              </div>
            </div>
          ))}
        </div>

        {/* Desktop table */}
        <div className="hidden sm:block overflow-x-auto">
          <table className="w-full text-xs" aria-label="Supplier ranking table">
            <thead className="bg-[var(--surface-subtle)] border-b border-[var(--divider)] text-[var(--text-secondary)]">
              <tr>
                <th scope="col" className="py-3 px-4 text-left font-semibold">Rank</th>
                <th scope="col" className="py-3 px-4 text-left font-semibold">Supplier</th>
                <th scope="col" className="py-3 px-4 text-left font-semibold">Country</th>
                <th scope="col" className="py-3 px-4 text-right font-semibold">Score</th>
                <th scope="col" className="py-3 px-4 text-right font-semibold">Landed Cost</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[var(--divider)]">
              {rec.ranking.map((r) => (
                <tr key={r.supplier_id} className={`hover:bg-[var(--surface-subtle)]/50 ${r.rank === 1 ? 'bg-[var(--brand-subtle)]/20' : ''}`}>
                  <td className="py-3 px-4 font-mono font-bold text-[var(--text-secondary)]">#{r.rank}</td>
                  <td className="py-3 px-4 font-semibold text-[var(--text-primary)]">
                    {r.rank === 1 && <span className="inline-block w-2 h-2 rounded-full bg-[var(--brand)] mr-2" aria-hidden="true" />}
                    {r.supplier_name}
                  </td>
                  <td className="py-3 px-4 text-[var(--text-secondary)]">{r.country}</td>
                  <td className="py-3 px-4 text-right font-bold num-tabular text-[var(--text-primary)]">{r.final_score.toFixed(1)}</td>
                  <td className="py-3 px-4 text-right num-tabular text-[var(--text-secondary)]">${r.scores.landed_cost.toFixed(2)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* ── Report history ── */}
      <div className="bg-[var(--surface)] rounded-xl border border-[var(--border)] overflow-hidden shadow-[var(--shadow-card)]">
        <div className="px-4 sm:px-5 py-4 border-b border-[var(--border)] flex items-center gap-2">
          <History className="w-4 h-4 text-[var(--brand)]" />
          <h3 className="text-sm font-bold text-[var(--text-primary)]">Report History</h3>
          <span className="ml-auto text-[11px] text-[var(--text-muted)]">Last 10 reports</span>
        </div>

        {historyReports.length === 0 ? (
          <EmptyState
            title="No saved reports"
            description="Download a PDF report to save it to history."
            icon={History}
          />
        ) : (
          <ul className="divide-y divide-[var(--divider)]">
            <AnimatePresence initial={false}>
              {historyReports.map((report) => (
                <motion.li
                  key={report.id}
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  exit={{ opacity: 0, height: 0 }}
                  transition={{ duration: 0.2 }}
                  className="flex items-center justify-between px-4 sm:px-5 py-3 hover:bg-[var(--surface-subtle)]/50 gap-3"
                >
                  <div className="flex items-center gap-3 min-w-0">
                    <Clock className="w-3.5 h-3.5 text-[var(--text-muted)] shrink-0" />
                    <div className="min-w-0">
                      <div className="text-xs font-semibold text-[var(--text-primary)] truncate max-w-[200px] sm:max-w-[280px]">
                        {report.title}
                      </div>
                      <div className="text-[10px] text-[var(--text-muted)] mt-0.5">
                        {new Date(report.created_at).toLocaleString('en-GB', { dateStyle: 'medium', timeStyle: 'short' })}
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-2 shrink-0">
                    <Badge variant="outline">{report.report_type}</Badge>
                    <button
                      onClick={() => deleteReportMutation.mutate(report.id)}
                      disabled={deleteReportMutation.isPending}
                      aria-label={`Delete report: ${report.title}`}
                      className="text-[var(--danger)] hover:opacity-70 transition-opacity disabled:opacity-40 p-1"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </motion.li>
              ))}
            </AnimatePresence>
          </ul>
        )}
      </div>

      {/* ── Disclaimer ── */}
      <p className="text-[11px] text-[var(--text-muted)] bg-[var(--surface-subtle)] p-3 rounded-lg border border-[var(--border)] leading-relaxed">
        This analysis is AI-assisted decision support. Legal, regulatory, and engineering advice
        requires human expert verification.
      </p>
    </div>
  );
}
