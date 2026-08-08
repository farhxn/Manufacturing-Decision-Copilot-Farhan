'use client';

/**
 * EvidencePanel — slide-out drawer showing evidence chunks for a recommendation.
 *
 * Opens from the right side of the screen. Fetches evidence by recommendation_id,
 * groups items by source document, and renders each chunk with EvidenceHighlight.
 * Clicking a chunk item can open the document viewer at the correct page.
 */

import React, { useEffect, useRef } from 'react';
import Link from 'next/link';
import { useQuery } from '@tanstack/react-query';
import { X, ExternalLink, FileText, Loader2, BookOpen } from 'lucide-react';
import { evidenceApi } from '@/services/api/evidenceApi';
import { EvidenceHighlight } from '@/components/documents/EvidenceHighlight';
import { EmptyState } from '@/components/ui/EmptyState';
import type { EvidenceItem } from '@/types';

interface EvidencePanelProps {
  /** Whether the drawer is visible */
  isOpen: boolean;
  /** Callback to close the panel */
  onClose: () => void;
  /** recommendation_id to fetch evidence for */
  recommendationId: string | null;
  /** Optional search phrase to highlight inside chunks */
  highlightPhrase?: string;
}

/** Group evidence items by source document */
function groupByDocument(items: EvidenceItem[]): Map<string, EvidenceItem[]> {
  const map = new Map<string, EvidenceItem[]>();
  for (const item of items) {
    const key = item.document_filename ?? item.document_id ?? 'Unknown document';
    if (!map.has(key)) map.set(key, []);
    map.get(key)!.push(item);
  }
  return map;
}

export function EvidencePanel({
  isOpen,
  onClose,
  recommendationId,
  highlightPhrase,
}: EvidencePanelProps) {
  const panelRef = useRef<HTMLDivElement>(null);

  // Close on Escape key
  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (e.key === 'Escape') onClose();
    }
    if (isOpen) window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [isOpen, onClose]);

  // Trap focus back to panel when it opens
  useEffect(() => {
    if (isOpen) panelRef.current?.focus();
  }, [isOpen]);

  const { data, isLoading, isError } = useQuery({
    queryKey: ['evidence', recommendationId],
    queryFn: () => evidenceApi.getByRecommendation(recommendationId!),
    enabled: isOpen && !!recommendationId,
    staleTime: 60_000,
  });

  const items  = data?.items ?? [];
  const groups = groupByDocument(items);

  return (
    <>
      {/* Backdrop */}
      <div
        className={`fixed inset-0 z-40 bg-black/30 backdrop-blur-sm transition-opacity duration-200 ${
          isOpen ? 'opacity-100 pointer-events-auto' : 'opacity-0 pointer-events-none'
        }`}
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Drawer */}
      <div
        ref={panelRef}
        tabIndex={-1}
        role="dialog"
        aria-modal="true"
        aria-label="Evidence Panel"
        className={`fixed top-0 right-0 z-50 h-full w-full max-w-lg bg-[var(--surface)] shadow-2xl
          flex flex-col outline-none transition-transform duration-300 ease-out
          ${isOpen ? 'translate-x-0' : 'translate-x-full'}`}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-[var(--border)] shrink-0">
          <div className="flex items-center gap-2">
            <BookOpen className="w-4 h-4 text-[var(--brand)]" />
            <h2 className="text-sm font-bold text-[var(--text-primary)]">Evidence</h2>
            {items.length > 0 && (
              <span className="text-[11px] font-semibold text-[var(--brand)] bg-[var(--brand-subtle)] px-2 py-0.5 rounded-full">
                {items.length} excerpts
              </span>
            )}
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg hover:bg-[var(--surface-subtle)] text-[var(--text-secondary)] transition-colors"
            aria-label="Close evidence panel"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Body */}
        <div className="flex-1 overflow-y-auto px-5 py-4 space-y-5">
          {/* Loading */}
          {isLoading && (
            <div className="flex flex-col items-center justify-center py-16 gap-3">
              <Loader2 className="w-6 h-6 text-[var(--brand)] animate-spin" />
              <span className="text-xs text-[var(--text-muted)]">Loading evidence…</span>
            </div>
          )}

          {/* Error */}
          {isError && (
            <div className="text-xs text-[var(--danger)] bg-[var(--danger-subtle)] p-3 rounded-lg border border-[var(--danger)]/30">
              Could not load evidence. Check that a recommendation has been generated.
            </div>
          )}

          {/* Empty */}
          {!isLoading && !isError && items.length === 0 && (
            <EmptyState
              title="No evidence yet"
              description="Generate a recommendation with AI to see supporting excerpts from uploaded documents."
              icon={FileText}
            />
          )}

          {/* Grouped by document */}
          {!isLoading && [...groups.entries()].map(([docName, docItems]) => (
            <div key={docName} className="space-y-2">
              {/* Document header */}
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-1.5 min-w-0">
                  <FileText className="w-3.5 h-3.5 text-[var(--text-muted)] shrink-0" />
                  <span className="text-[11px] font-bold text-[var(--text-secondary)] truncate">
                    {docName}
                  </span>
                </div>
                {docItems[0].document_id && (
                  <Link
                    href={`/documents/${docItems[0].document_id}`}
                    className="shrink-0 inline-flex items-center gap-1 text-[10px] font-semibold text-[var(--brand)] hover:underline"
                    onClick={onClose}
                  >
                    Open <ExternalLink className="w-3 h-3" />
                  </Link>
                )}
              </div>

              {/* Chunks */}
              <div className="space-y-2">
                {docItems
                  .sort((a, b) => b.relevance_score - a.relevance_score)
                  .map((item) => (
                    <EvidenceHighlight
                      key={item.id}
                      text={item.snippet}
                      highlight={highlightPhrase}
                      sourceDocument={undefined}   // already shown in group header
                      pageNumber={item.page_number ?? undefined}
                      relevanceScore={item.relevance_score}
                      chunkIndex={undefined}
                    />
                  ))}
              </div>
            </div>
          ))}
        </div>

        {/* Footer hint */}
        <div className="px-5 py-3 border-t border-[var(--border)] shrink-0">
          <p className="text-[10px] text-[var(--text-muted)]">
            Evidence sourced from uploaded supplier documents via hybrid BM25 + vector retrieval.
            Click &ldquo;Open&rdquo; to view the source document.
          </p>
        </div>
      </div>
    </>
  );
}
