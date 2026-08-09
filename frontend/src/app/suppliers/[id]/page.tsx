'use client';

import React, { useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { useQuery } from '@tanstack/react-query';
import {
  ArrowLeft, ShieldCheck, Package, MapPin,
  Clock, DollarSign, TrendingUp, CheckCircle2, X, BookOpen,
} from 'lucide-react';
import { supplierApi } from '@/services/api/supplierApi';
import { recommendationApi } from '@/services/api/recommendationApi';
import { EvidencePanel } from '@/components/suppliers/EvidencePanel';
import { Badge } from '@/components/ui/Badge';
import { SkeletonCard } from '@/components/ui/Skeleton';
import { ErrorState } from '@/components/ui/ErrorState';
import { getActiveWorkspaceId, useWorkspaceStore } from '@/store/workspaceStore';

function ScoreBar({ label, value }: { label: string; value: number }) {
  const color = value >= 70 ? 'var(--success)' : value >= 45 ? 'var(--warning)' : 'var(--danger)';
  return (
    <div className="space-y-1">
      <div className="flex justify-between text-xs">
        <span className="text-[var(--text-secondary)]">{label}</span>
        <span className="font-bold num-tabular text-[var(--text-primary)]">{value.toFixed(1)}</span>
      </div>
      <div className="h-2 bg-[var(--surface-subtle)] rounded-full overflow-hidden">
        <div
          className="h-full rounded-full transition-all duration-500"
          style={{ width: `${value}%`, background: color }}
        />
      </div>
    </div>
  );
}

export default function SupplierDetailPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const [evidenceOpen, setEvidenceOpen] = useState(false);

  const activeWorkspaceId = useWorkspaceStore(state => state.activeWorkspaceId);
  const currentProjectId  = activeWorkspaceId || getActiveWorkspaceId();

  const { data: supplier, isLoading, isError, refetch } = useQuery({
    queryKey: ['supplier', id],
    queryFn:  () => supplierApi.getById(id),
    enabled:  !!id,
  });

  const { data: rec } = useQuery({
    queryKey: ['recommendation', currentProjectId],
    queryFn:  () => recommendationApi.get(currentProjectId),
    staleTime: 60_000,
  });

  if (isLoading) return (
    <div className="max-w-5xl mx-auto space-y-4 pb-12">
      <SkeletonCard lines={2} />
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        <SkeletonCard lines={5} />
        <SkeletonCard lines={5} />
        <SkeletonCard lines={5} />
      </div>
    </div>
  );

  if (isError || !supplier) return (
    <ErrorState title="Supplier not found" onRetry={() => refetch()} />
  );

  const riskVariant = supplier.risk_level === 'Low' ? 'success'
    : supplier.risk_level === 'Medium' ? 'warning' : 'danger';

  const evidenceId = rec?.id ?? currentProjectId;

  return (
    <div className="max-w-5xl mx-auto space-y-4 sm:space-y-6 pb-12">

      {/* ── Nav + actions ── */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <button
          onClick={() => router.back()}
          className="flex items-center gap-2 text-xs text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-colors self-start"
        >
          <ArrowLeft className="w-4 h-4" /> Back to suppliers
        </button>
        <div className="flex items-center gap-2 flex-wrap">
          <Badge variant={riskVariant as 'success' | 'warning' | 'danger'}>{supplier.risk_level} Risk</Badge>
          <Badge variant={supplier.status === 'active' ? 'success' : 'outline'}>{supplier.status}</Badge>
          <button
            onClick={() => setEvidenceOpen(true)}
            className="inline-flex items-center gap-1.5 px-3 sm:px-3.5 py-2 text-xs font-semibold rounded-lg bg-[var(--brand)] text-white hover:opacity-90 transition-all"
          >
            <BookOpen className="w-3.5 h-3.5" />
            View Evidence
          </button>
        </div>
      </div>

      {/* ── Hero card ── */}
      <div className="bg-[var(--surface)] rounded-xl border border-[var(--border-strong)] border-l-4 border-l-[var(--brand)] p-4 sm:p-6 shadow-md">
        <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4">
          <div className="min-w-0">
            <h1 className="text-xl sm:text-2xl font-bold text-[var(--text-primary)] truncate">{supplier.name}</h1>
            <div className="flex flex-wrap items-center gap-2 sm:gap-3 text-xs text-[var(--text-secondary)] mt-2">
              <span className="flex items-center gap-1">
                <MapPin className="w-3.5 h-3.5 shrink-0" />
                {supplier.city ? `${supplier.city}, ` : ''}{supplier.country}
              </span>
              <span className="flex items-center gap-1">
                <DollarSign className="w-3.5 h-3.5 shrink-0" />
                {supplier.currency} {supplier.unit_price.toFixed(2)} / unit
              </span>
              <span className="flex items-center gap-1">
                <Clock className="w-3.5 h-3.5 shrink-0" />
                {supplier.lead_time_days} days lead time
              </span>
              <span className="flex items-center gap-1">
                <Package className="w-3.5 h-3.5 shrink-0" />
                MOQ: {supplier.moq}
              </span>
            </div>
          </div>
          {/* Score box — aligns right on sm+, left-aligned row on xs */}
          <div className="flex sm:flex-col sm:text-right items-center sm:items-end gap-3 sm:gap-0 shrink-0">
            <div>
              <div className="text-[10px] text-[var(--text-muted)] uppercase font-mono">Composite Score</div>
              <div className="text-3xl font-extrabold text-[var(--brand)] num-tabular leading-none">
                {supplier.scores.final_score.toFixed(1)}
              </div>
            </div>
            <div className="text-[11px] text-[var(--text-muted)] sm:mt-0.5">
              Rank #{supplier.scores.rank ?? '—'}
            </div>
          </div>
        </div>
      </div>

      {/* ── 3-col detail grid: 1-col xs → 2-col sm → 3-col lg ── */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6">

        {/* Score breakdown */}
        <div className="sm:col-span-2 lg:col-span-1 bg-[var(--surface)] rounded-xl border border-[var(--border)] p-4 sm:p-5 shadow-[var(--shadow-card)] space-y-4">
          <h3 className="text-sm font-bold text-[var(--text-primary)] flex items-center gap-2">
            <TrendingUp className="w-4 h-4 text-[var(--brand)]" /> Score Breakdown
          </h3>
          <ScoreBar label="Cost Score"       value={supplier.scores.cost_score} />
          <ScoreBar label="Quality Score"    value={supplier.scores.quality_score} />
          <ScoreBar label="Delivery Score"   value={supplier.scores.delivery_score} />
          <ScoreBar label="Risk Score"       value={supplier.scores.risk_score} />
          <ScoreBar label="Capability Score" value={supplier.scores.capability_score} />
          <ScoreBar label="Compliance Score" value={supplier.scores.compliance_score} />
          <div className="pt-2 border-t border-[var(--divider)]">
            <div className="flex justify-between text-xs font-bold">
              <span className="text-[var(--text-primary)]">Landed Cost</span>
              <span className="num-tabular text-[var(--text-primary)]">
                ${supplier.scores.landed_cost.toFixed(2)}
              </span>
            </div>
          </div>
        </div>

        {/* Certifications */}
        <div className="bg-[var(--surface)] rounded-xl border border-[var(--border)] p-4 sm:p-5 shadow-[var(--shadow-card)] space-y-4">
          <h3 className="text-sm font-bold text-[var(--text-primary)] flex items-center gap-2">
            <ShieldCheck className="w-4 h-4 text-[var(--brand)]" /> Certifications
          </h3>
          {supplier.certifications.length === 0 ? (
            <div className="text-xs text-[var(--text-muted)] italic">No certifications on record.</div>
          ) : (
            <ul className="space-y-2">
              {supplier.certifications.map((c, i) => (
                <li key={i} className="flex items-center justify-between text-xs gap-2">
                  <div className="flex items-center gap-2 min-w-0">
                    {c.is_valid
                      ? <CheckCircle2 className="w-3.5 h-3.5 text-[var(--success)] shrink-0" />
                      : <X className="w-3.5 h-3.5 text-[var(--danger)] shrink-0" />}
                    <span className="font-semibold text-[var(--text-primary)] truncate">{c.name}</span>
                  </div>
                  <span className="text-[var(--text-muted)] shrink-0">{c.issuer ?? '—'}</span>
                </li>
              ))}
            </ul>
          )}
        </div>

        {/* Capabilities */}
        <div className="bg-[var(--surface)] rounded-xl border border-[var(--border)] p-4 sm:p-5 shadow-[var(--shadow-card)] space-y-4">
          <h3 className="text-sm font-bold text-[var(--text-primary)] flex items-center gap-2">
            <Package className="w-4 h-4 text-[var(--brand)]" /> Capabilities
          </h3>
          {supplier.capabilities.length === 0 ? (
            <div className="text-xs text-[var(--text-muted)] italic">No capabilities on record.</div>
          ) : (
            <div className="flex flex-wrap gap-2">
              {supplier.capabilities.map((c, i) => (
                <Badge key={i} variant={c.verified ? 'brand' : 'outline'}>
                  {c.name}
                </Badge>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Evidence panel drawer */}
      <EvidencePanel
        isOpen={evidenceOpen}
        onClose={() => setEvidenceOpen(false)}
        recommendationId={evidenceId}
        recommendation={rec}
        highlightPhrase={supplier.name}
      />
    </div>
  );
}
