'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { useQuery } from '@tanstack/react-query';
import { Search, ExternalLink, ArrowUpDown, ChevronDown } from 'lucide-react';
import { motion } from 'framer-motion';
import { listVariants, itemVariants, denseListVariants } from '@/lib/motionVariants';
import { supplierApi } from '@/services/api/supplierApi';
import { Badge } from '@/components/ui/Badge';
import { SkeletonTable } from '@/components/ui/Skeleton';
import { ErrorState } from '@/components/ui/ErrorState';
import { EmptyState } from '@/components/ui/EmptyState';
import { SupplierFormModal } from '@/components/suppliers/SupplierFormModal';
import { useWorkspaceStore } from '@/store/workspaceStore';
import type { SupplierSummary, SupplierCreateRequest, SupplierUpdateRequest } from '@/types';

type SortKey = 'rank' | 'name' | 'landed_cost' | 'lead_time_days' | 'final_score';
type SortDir = 'asc' | 'desc';

function riskBadge(level: string) {
  if (level === 'Low') return <Badge variant="success">Low</Badge>;
  if (level === 'Medium') return <Badge variant="warning">Medium</Badge>;
  return <Badge variant="danger">High</Badge>;
}

export default function SuppliersPage() {
  const [search, setSearch] = useState('');
  const [sortKey, setSortKey] = useState<SortKey>('final_score');
  const [sortDir, setSortDir] = useState<SortDir>('desc');
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingSupplier, setEditingSupplier] = useState<SupplierSummary | undefined>(undefined);

  const { activeWorkspaceId } = useWorkspaceStore();

  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ['suppliers', activeWorkspaceId, search],
    queryFn: () => supplierApi.list({ project_id: activeWorkspaceId || undefined, search: search || undefined, limit: 50 }),
  });

  const suppliers: SupplierSummary[] = data?.data ?? [];

  const sorted = [...suppliers].sort((a, b) => {
    let av: number | string = 0, bv: number | string = 0;
    if (sortKey === 'rank')             { av = a.scores.rank ?? 99; bv = b.scores.rank ?? 99; }
    else if (sortKey === 'name')        { av = a.name; bv = b.name; }
    else if (sortKey === 'landed_cost') { av = a.landed_cost; bv = b.landed_cost; }
    else if (sortKey === 'lead_time_days') { av = a.lead_time_days; bv = b.lead_time_days; }
    else if (sortKey === 'final_score') { av = a.scores.final_score; bv = b.scores.final_score; }
    if (typeof av === 'string') return sortDir === 'asc' ? av.localeCompare(bv as string) : (bv as string).localeCompare(av);
    return sortDir === 'asc' ? (av as number) - (bv as number) : (bv as number) - (av as number);
  });

  function toggleSort(key: SortKey) {
    if (sortKey === key) setSortDir(d => d === 'asc' ? 'desc' : 'asc');
    else { setSortKey(key); setSortDir('desc'); }
  }

  const handleCreateOrUpdate = async (formData: SupplierCreateRequest | SupplierUpdateRequest) => {
    if (editingSupplier) {
      await supplierApi.update(editingSupplier.id, formData as SupplierUpdateRequest);
    } else {
      await supplierApi.create(formData as SupplierCreateRequest);
    }
    refetch();
  };

  const handleDelete = async (id: string) => {
    if (confirm('Are you sure you want to delete this supplier?')) {
      try {
        await supplierApi.delete(id);
        refetch();
      } catch (err: unknown) {
        alert((err as Error).message || 'Failed to delete supplier');
      }
    }
  };

  const openEditModal = (supplier: SupplierSummary) => { setEditingSupplier(supplier); setIsModalOpen(true); };
  const openCreateModal = () => { setEditingSupplier(undefined); setIsModalOpen(true); };

  const Th = ({ label, sortable, k }: { label: string; sortable?: SortKey; k?: string }) => (
    <th className="py-3 px-4 text-left text-xs font-semibold text-[var(--text-secondary)] whitespace-nowrap" key={k}>
      {sortable ? (
        <button onClick={() => toggleSort(sortable)} className="flex items-center gap-1 hover:text-[var(--text-primary)]">
          {label} <ArrowUpDown className="w-3 h-3" />
        </button>
      ) : label}
    </th>
  );

  return (
    <div className="max-w-7xl mx-auto space-y-4 sm:space-y-6 pb-12">

      {/* ── Page Header ─────────────────────────────────────────────── */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <div>
          <h1 className="text-xl font-bold text-[var(--text-primary)]">Suppliers</h1>
          <p className="text-xs text-[var(--text-secondary)] mt-0.5">
            {suppliers.length} vendors evaluated · sorted by {sortKey.replace(/_/g, ' ')}
          </p>
        </div>
        <div className="flex items-center gap-2 sm:gap-3">
          <div className="relative flex-1 sm:flex-none">
            <Search className="w-3.5 h-3.5 absolute left-3 top-1/2 -translate-y-1/2 text-[var(--text-muted)]" />
            <input
              type="text"
              placeholder="Search suppliers…"
              value={search}
              onChange={e => setSearch(e.target.value)}
              className="pl-9 pr-4 py-2 text-xs rounded-lg bg-[var(--surface)] border border-[var(--border)] text-[var(--text-primary)] placeholder:text-[var(--text-muted)] focus:outline-none focus:border-[var(--brand)] w-full sm:w-56 lg:w-72 transition-all"
            />
          </div>
          {/* Mobile sort picker */}
          <div className="relative sm:hidden">
            <select
              value={sortKey}
              onChange={e => setSortKey(e.target.value as SortKey)}
              className="appearance-none pl-3 pr-7 py-2 text-xs rounded-lg bg-[var(--surface)] border border-[var(--border)] text-[var(--text-primary)] focus:outline-none focus:border-[var(--brand)]"
            >
              <option value="final_score">Score</option>
              <option value="rank">Rank</option>
              <option value="name">Name</option>
              <option value="landed_cost">Cost</option>
              <option value="lead_time_days">Lead Time</option>
            </select>
            <ChevronDown className="w-3 h-3 absolute right-2 top-1/2 -translate-y-1/2 text-[var(--text-muted)] pointer-events-none" />
          </div>
          <button
            onClick={openCreateModal}
            className="px-3 sm:px-4 py-2 text-xs font-semibold rounded-lg bg-[var(--brand)] text-white hover:bg-[var(--brand-hover)] transition-all whitespace-nowrap"
          >
            + Supplier
          </button>
        </div>
      </div>

      {isLoading && <SkeletonTable rows={5} />}
      {isError && <ErrorState onRetry={() => refetch()} message="Could not load suppliers." />}
      {!isLoading && !isError && sorted.length === 0 && (
        <EmptyState title="No suppliers found" description="Try a different search term or seed the database." />
      )}

      {!isLoading && !isError && sorted.length > 0 && (
        <>
          {/* ── Mobile Card View (xs only) ────────────────────────── */}
          <motion.div
            className="sm:hidden space-y-3"
            variants={listVariants}
            initial="hidden"
            animate="show"
          >
            {sorted.map((s, idx) => (
              <motion.div
                key={s.id}
                variants={itemVariants}
                className={`bg-[var(--surface)] rounded-xl border shadow-[var(--shadow-card)] p-4 space-y-3 ${
                  idx === 0 ? 'border-[var(--brand)]/40' : 'border-[var(--border)]'
                }`}
              >
                {/* Card header row */}
                <div className="flex items-start justify-between gap-2">
                  <div className="min-w-0">
                    <div className="flex items-center gap-2 mb-0.5">
                      <span className="font-mono text-[11px] text-[var(--text-muted)]">
                        #{s.scores.rank ?? idx + 1}
                      </span>
                      {idx === 0 && (
                        <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-[var(--brand-subtle)] text-[var(--brand)] border border-[var(--brand)]/30">
                          #1
                        </span>
                      )}
                    </div>
                    <div className="font-semibold text-sm text-[var(--text-primary)] truncate">{s.name}</div>
                    {s.city && <div className="text-[11px] text-[var(--text-muted)]">{s.city}, {s.country}</div>}
                    {!s.city && <div className="text-[11px] text-[var(--text-muted)]">{s.country}</div>}
                  </div>
                  <div className="shrink-0 text-right">
                    <div className="text-lg font-bold text-[var(--text-primary)] num-tabular">
                      {s.scores.final_score.toFixed(1)}
                    </div>
                    <div className="text-[10px] text-[var(--text-muted)]">/ 100</div>
                  </div>
                </div>

                {/* Score bar */}
                <div className="w-full bg-[var(--surface-subtle)] h-1.5 rounded-full overflow-hidden">
                  <div
                    className="h-full rounded-full bg-[var(--brand)]"
                    style={{ width: `${s.scores.final_score}%` }}
                  />
                </div>

                {/* Stats grid */}
                <div className="grid grid-cols-3 gap-2 text-xs">
                  <div>
                    <div className="text-[var(--text-muted)] text-[10px]">Unit Price</div>
                    <div className="font-semibold text-[var(--text-primary)] num-tabular">
                      {s.currency} {s.unit_price.toFixed(2)}
                    </div>
                  </div>
                  <div>
                    <div className="text-[var(--text-muted)] text-[10px]">Landed Cost</div>
                    <div className="font-semibold text-[var(--text-primary)] num-tabular">
                      ${s.landed_cost.toFixed(2)}
                    </div>
                  </div>
                  <div>
                    <div className="text-[var(--text-muted)] text-[10px]">Lead Time</div>
                    <div className="font-semibold text-[var(--text-primary)] num-tabular">
                      {s.lead_time_days}d
                    </div>
                  </div>
                </div>

                {/* Risk + actions row */}
                <div className="flex items-center justify-between pt-1 border-t border-[var(--divider)]">
                  <div className="flex items-center gap-2">
                    {riskBadge(s.risk_level)}
                  </div>
                  <div className="flex items-center gap-3 text-xs">
                    <button
                      onClick={() => openEditModal(s)}
                      className="text-[var(--text-secondary)] hover:text-[var(--text-primary)] font-semibold transition-colors"
                    >
                      Edit
                    </button>
                    <button
                      onClick={() => handleDelete(s.id)}
                      className="text-[var(--danger)] font-semibold transition-colors"
                    >
                      Delete
                    </button>
                    <Link
                      href={`/suppliers/${s.id}`}
                      className="text-[var(--brand)] font-semibold inline-flex items-center gap-1 pl-3 border-l border-[var(--divider)]"
                    >
                      View <ExternalLink className="w-3 h-3" />
                    </Link>
                  </div>
                </div>
              </motion.div>
            ))}
          </motion.div>

          {/* ── Desktop Table View (sm+) ──────────────────────────── */}
          <div className="hidden sm:block bg-[var(--surface)] rounded-xl border border-[var(--border)] overflow-hidden shadow-[var(--shadow-card)]">
            <div className="overflow-x-auto">
              <table className="w-full text-xs">
                <thead className="bg-[var(--surface-subtle)] border-b border-[var(--border)]">
                  <tr>
                    <Th label="Rank"        sortable="rank"            k="rank" />
                    <Th label="Supplier"    sortable="name"            k="name" />
                    <Th label="Country"                                k="country" />
                    <Th label="Unit Price"                             k="price" />
                    <Th label="Landed Cost" sortable="landed_cost"     k="cost" />
                    <Th label="Lead Time"   sortable="lead_time_days"  k="lt" />
                    <Th label="Risk"                                   k="risk" />
                    <Th label="Score"       sortable="final_score"     k="score" />
                    <Th label="Actions"                                k="actions" />
                  </tr>
                </thead>
                <tbody className="divide-y divide-[var(--divider)]">
                  {sorted.map((s, idx) => (
                    <tr
                      key={s.id}
                      className={`hover:bg-[var(--surface-subtle)]/60 transition-colors ${idx === 0 ? 'bg-[var(--brand-subtle)]/20' : ''}`}
                    >
                      <td className="py-3 px-4 font-mono font-bold text-[var(--text-secondary)]">
                        #{s.scores.rank ?? idx + 1}
                      </td>
                      <td className="py-3 px-4 font-semibold text-[var(--text-primary)]">
                        <div className="flex items-center gap-2">
                          {idx === 0 && <span className="w-2 h-2 rounded-full bg-[var(--brand)] shrink-0" />}
                          {s.name}
                        </div>
                        {s.city && <div className="text-[11px] text-[var(--text-muted)]">{s.city}</div>}
                      </td>
                      <td className="py-3 px-4 text-[var(--text-secondary)]">{s.country}</td>
                      <td className="py-3 px-4 num-tabular text-[var(--text-primary)]">
                        {s.currency} {s.unit_price.toFixed(2)}
                      </td>
                      <td className="py-3 px-4 num-tabular font-medium text-[var(--text-primary)]">
                        ${s.landed_cost.toFixed(2)}
                      </td>
                      <td className="py-3 px-4 num-tabular text-[var(--text-secondary)]">
                        {s.lead_time_days}d
                      </td>
                      <td className="py-3 px-4">{riskBadge(s.risk_level)}</td>
                      <td className="py-3 px-4 font-bold num-tabular text-[var(--text-primary)]">
                        <div className="flex items-center gap-2">
                          {s.scores.final_score.toFixed(1)}
                          <div className="bg-[var(--surface-subtle)] h-1.5 rounded-full w-16 overflow-hidden">
                            <div
                              className="h-full rounded-full bg-[var(--brand)]"
                              style={{ width: `${s.scores.final_score}%` }}
                            />
                          </div>
                        </div>
                      </td>
                      <td className="py-3 px-4">
                        <div className="flex items-center gap-3">
                          <button
                            onClick={() => openEditModal(s)}
                            className="text-[var(--text-secondary)] hover:text-[var(--text-primary)] text-xs font-semibold transition-colors"
                          >
                            Edit
                          </button>
                          <button
                            onClick={() => handleDelete(s.id)}
                            className="text-[var(--danger)] text-xs font-semibold transition-colors"
                          >
                            Delete
                          </button>
                          <Link
                            href={`/suppliers/${s.id}`}
                            className="text-[var(--brand)] hover:underline font-semibold text-xs inline-flex items-center gap-1 ml-2 border-l border-[var(--divider)] pl-3"
                          >
                            View <ExternalLink className="w-3 h-3" />
                          </Link>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}

      <SupplierFormModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onSubmit={handleCreateOrUpdate}
        initialData={editingSupplier}
        isEditing={!!editingSupplier}
      />
    </div>
  );
}
