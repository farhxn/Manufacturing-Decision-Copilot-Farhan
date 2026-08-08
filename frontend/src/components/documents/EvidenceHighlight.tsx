'use client';

/**
 * EvidenceHighlight — inline text display component.
 *
 * Shows an evidence chunk snippet with the matched search term highlighted
 * in yellow. Used inside the EvidencePanel drawer and the document chunks list
 * to visually call out the exact extracted passage.
 *
 * Does NOT depend on PDF.js — it works on the plain text content stored in
 * PostgreSQL (document_chunks.content). The DocumentViewer handles the
 * canvas-level highlight inside the actual PDF rendering.
 */

import React from 'react';
import { FileText, Hash } from 'lucide-react';

interface EvidenceHighlightProps {
  /** Full chunk text to display */
  text: string;
  /** Search phrase to highlight — case-insensitive, highlights first match */
  highlight?: string;
  /** Source document filename */
  sourceDocument?: string;
  /** Page number within the source document */
  pageNumber?: number;
  /** Relevance score 0–1 */
  relevanceScore?: number;
  /** Chunk index */
  chunkIndex?: number;
  className?: string;
}

/**
 * Split `text` into parts around the first occurrence of `needle` (case-insensitive).
 * Returns an array of { part: string; highlighted: boolean }.
 */
function splitHighlight(
  text: string,
  needle: string,
): Array<{ part: string; highlighted: boolean }> {
  if (!needle.trim()) return [{ part: text, highlighted: false }];

  const idx = text.toLowerCase().indexOf(needle.toLowerCase());
  if (idx === -1) return [{ part: text, highlighted: false }];

  return [
    { part: text.slice(0, idx),              highlighted: false },
    { part: text.slice(idx, idx + needle.length), highlighted: true },
    { part: text.slice(idx + needle.length), highlighted: false },
  ];
}

function ScoreBar({ score }: { score: number }) {
  const pct   = Math.round(score * 100);
  const color = score >= 0.7 ? 'var(--success)' : score >= 0.4 ? 'var(--warning)' : 'var(--danger)';
  return (
    <div className="flex items-center gap-1.5">
      <div className="w-16 h-1.5 bg-[var(--surface-subtle)] rounded-full overflow-hidden border border-[var(--border)]">
        <div className="h-full rounded-full" style={{ width: `${pct}%`, background: color }} />
      </div>
      <span className="text-[10px] font-mono text-[var(--text-muted)]">{pct}%</span>
    </div>
  );
}

export function EvidenceHighlight({
  text,
  highlight,
  sourceDocument,
  pageNumber,
  relevanceScore,
  chunkIndex,
  className = '',
}: EvidenceHighlightProps) {
  const parts = highlight ? splitHighlight(text, highlight) : [{ part: text, highlighted: false }];

  return (
    <div className={`rounded-lg border border-[var(--border)] bg-[var(--surface)] overflow-hidden ${className}`}>
      {/* Header */}
      {(sourceDocument || pageNumber !== undefined || chunkIndex !== undefined) && (
        <div className="flex items-center justify-between px-3 py-2 bg-[var(--surface-subtle)] border-b border-[var(--border)]">
          <div className="flex items-center gap-2 min-w-0">
            <FileText className="w-3.5 h-3.5 text-[var(--brand)] shrink-0" />
            {sourceDocument && (
              <span className="text-[11px] font-semibold text-[var(--text-secondary)] truncate max-w-[200px]">
                {sourceDocument}
              </span>
            )}
            {pageNumber !== undefined && (
              <span className="text-[10px] text-[var(--text-muted)] shrink-0">p.{pageNumber}</span>
            )}
            {chunkIndex !== undefined && (
              <span className="inline-flex items-center gap-0.5 text-[10px] font-mono text-[var(--brand)] bg-[var(--brand-subtle)] px-1.5 py-0.5 rounded shrink-0">
                <Hash className="w-2.5 h-2.5" />{chunkIndex}
              </span>
            )}
          </div>
          {relevanceScore !== undefined && <ScoreBar score={relevanceScore} />}
        </div>
      )}

      {/* Text body with inline highlight */}
      <p className="px-3 py-2.5 text-xs text-[var(--text-secondary)] leading-relaxed">
        {parts.map((p, i) =>
          p.highlighted ? (
            <mark
              key={i}
              className="bg-yellow-200 text-yellow-900 rounded px-0.5 not-italic font-semibold"
            >
              {p.part}
            </mark>
          ) : (
            <span key={i}>{p.part}</span>
          )
        )}
      </p>
    </div>
  );
}
