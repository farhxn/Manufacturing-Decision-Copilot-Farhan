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
import type { EvidenceItem, Recommendation } from '@/types';

interface EvidencePanelProps {
  /** Whether the drawer is visible */
  isOpen: boolean;
  /** Callback to close the panel */
  onClose: () => void;
  /** recommendation_id to fetch evidence for */
  recommendationId: string | null;
  /** Optional recommendation object for synthesized fallback evidence */
  recommendation?: Recommendation | null;
  /** Optional search phrase to highlight inside chunks */
  highlightPhrase?: string;
}

/** Deduplicate evidence items by normalized snippet text */
export function deduplicateEvidenceItems(items: EvidenceItem[]): EvidenceItem[] {
  const seenTexts = new Set<string>();
  const uniqueItems: EvidenceItem[] = [];

  for (const item of items) {
    const norm = item.snippet.trim().toLowerCase().replace(/\s+/g, ' ').slice(0, 80);
    if (!norm || seenTexts.has(norm)) continue;
    seenTexts.add(norm);
    uniqueItems.push(item);
  }

  return uniqueItems;
}

/** Synthesize and deduplicate evidence items from recommendation object if DB is empty */
export function getUniqueEvidenceExcerpts(
  recommendation: Recommendation | undefined | null,
  apiItems: EvidenceItem[] = [],
  supplierNameOrId?: string
): EvidenceItem[] {
  let items: EvidenceItem[] = apiItems ?? [];

  if (items.length === 0 && recommendation) {
    const synth: EvidenceItem[] = [];

    // If viewing evidence for a specific supplier, focus ONLY on that supplier's citations
    const matchedSupplier = recommendation.ranking?.find(
      (r) =>
        (supplierNameOrId && r.supplier_name?.toLowerCase() === supplierNameOrId.toLowerCase()) ||
        r.supplier_id === supplierNameOrId
    );

    const supplierCitations = matchedSupplier ? matchedSupplier.citations : recommendation.ranking?.[0]?.citations;

    if (supplierCitations) {
      Object.entries(supplierCitations).forEach(([key, cit], idx) => {
        if (cit && cit.chunk_text) {
          synth.push({
            id: `supp-cit-${key}-${idx}`,
            chunk_id: `supp-chunk-${key}-${idx}`,
            document_id: cit.document_id || null,
            document_filename: cit.source_document || `${matchedSupplier?.supplier_name || 'Supplier'} Quotation.pdf`,
            snippet: cit.chunk_text,
            relevance_score: 0.96 - idx * 0.03,
            page_number: cit.page_number || 1,
          });
        }
      });
    }

    // Only include pros citations if viewing overall dashboard recommendation (not supplier-specific detail)
    if (!supplierNameOrId && recommendation.pros_citations && recommendation.pros_citations.length > 0) {
      recommendation.pros_citations.forEach((cit, idx) => {
        if (cit && cit.chunk_text) {
          synth.push({
            id: `pro-cit-${idx}`,
            chunk_id: `pro-chunk-${idx}`,
            document_id: cit.document_id || null,
            document_filename: cit.source_document || 'Supplier Evaluation Matrix.pdf',
            snippet: cit.chunk_text,
            relevance_score: 0.90 - idx * 0.03,
            page_number: cit.page_number || 1,
          });
        }
      });
    }

    items = synth;
  }

  return deduplicateEvidenceItems(items);
}

/** Return the exact number of unique evidence excerpts */
export function getUniqueEvidenceCount(
  recommendation: Recommendation | undefined | null,
  apiItems: EvidenceItem[] = [],
  supplierNameOrId?: string
): number {
  return getUniqueEvidenceExcerpts(recommendation, apiItems, supplierNameOrId).length;
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
  recommendation,
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

  const { data, isLoading } = useQuery({
    queryKey: ['evidence', recommendationId],
    queryFn: () => evidenceApi.getByRecommendation(recommendationId!),
    enabled: isOpen && !!recommendationId,
    staleTime: 60_000,
  });

  const items = getUniqueEvidenceExcerpts(recommendation, data?.items, highlightPhrase);
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
            <h2 className="text-sm font-bold text-[var(--text-primary)]">Evidence Excerpts</h2>
            {items.length > 0 && (
              <span className="text-[11px] font-semibold text-[var(--brand)] bg-[var(--brand-subtle)] px-2 py-0.5 rounded-full">
                {items.length} excerpt{items.length > 1 ? 's' : ''}
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

          {/* Empty */}
          {!isLoading && items.length === 0 && (
            <EmptyState
              title="No evidence excerpts found"
              description="No document excerpts were mapped for this decision yet."
              icon={FileText}
            />
          )}

          {/* Grouped by document */}
          {!isLoading && [...groups.entries()].map(([docName, docItems]) => (
            <div key={docName} className="space-y-2">
              {/* Document header */}
              <div className="flex items-center justify-between bg-[var(--surface-subtle)] p-2 rounded-lg border border-[var(--border)]">
                <div className="flex items-center gap-1.5 min-w-0">
                  <FileText className="w-3.5 h-3.5 text-[var(--brand)] shrink-0" />
                  <span className="text-[11px] font-bold text-[var(--text-primary)] truncate">
                    {docName}
                  </span>
                </div>
                <span className="text-[10px] font-mono text-[var(--text-muted)] bg-[var(--surface)] px-2 py-0.5 rounded border border-[var(--border)]">
                  {docItems.length} excerpt{docItems.length > 1 ? 's' : ''}
                </span>
              </div>

              {/* Chunks */}
              <div className="space-y-2.5 pl-1">
                {docItems
                  .sort((a, b) => b.relevance_score - a.relevance_score)
                  .map((item) => (
                    <div key={item.id} className="space-y-1">
                      <EvidenceHighlight
                        text={item.snippet}
                        highlight={highlightPhrase}
                        sourceDocument={undefined}   // shown in header
                        pageNumber={item.page_number ?? undefined}
                        relevanceScore={item.relevance_score}
                        chunkIndex={undefined}
                      />
                      {item.document_id && (
                        <div className="flex justify-end pr-1">
                          <Link
                            href={`/documents/${item.document_id}?page=${item.page_number || 1}`}
                            target="_blank"
                            className="inline-flex items-center gap-1 text-[10px] font-semibold text-[var(--brand)] hover:underline"
                            onClick={onClose}
                          >
                            Open PDF (Page {item.page_number || 1}) <ExternalLink className="w-2.5 h-2.5" />
                          </Link>
                        </div>
                      )}
                    </div>
                  ))}
              </div>
            </div>
          ))}
        </div>

        {/* Footer hint */}
        <div className="px-5 py-3 border-t border-[var(--border)] shrink-0">
          <p className="text-[10px] text-[var(--text-muted)]">
            Evidence grounded from ingested supplier documents.
            Click &ldquo;Open PDF&rdquo; to inspect the original document page.
          </p>
        </div>
      </div>
    </>
  );
}
