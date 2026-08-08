'use client';

import React, { useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { useQuery } from '@tanstack/react-query';
import { ArrowLeft, CheckCircle2, AlertCircle, Loader2, FileText, Eye } from 'lucide-react';
import { documentApi } from '@/services/api/documentApi';
import { DocumentViewer } from '@/components/documents/DocumentViewer';
import { EvidenceHighlight } from '@/components/documents/EvidenceHighlight';
import { Badge } from '@/components/ui/Badge';
import { SkeletonCard } from '@/components/ui/Skeleton';
import { ErrorState } from '@/components/ui/ErrorState';
import { EmptyState } from '@/components/ui/EmptyState';

// ── Constants ─────────────────────────────────────────────────────────────────

const STATUS_STEPS = ['uploaded', 'processing', 'extracting', 'indexing', 'completed'];

const PROGRESS_MAP: Record<string, number> = {
  uploaded: 5, processing: 20, extracting: 50, indexing: 80, completed: 100, error: 0,
};

function documentFileUrl(documentId: string): string {
  const base = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000/api/v1';
  return `${base.replace(/\/$/, '')}/documents/${documentId}/file`;
}

// ── Processing timeline — horizontal scroll on mobile ─────────────────────────

function ProcessingTimeline({ status }: { status: string }) {
  const current = STATUS_STEPS.indexOf(status);
  return (
    /* Outer div scrolls on xs so the 5-node pipeline never wraps */
    <div className="overflow-x-auto -mx-1 px-1 pb-2">
      <div className="flex items-start gap-0 min-w-max">
        {STATUS_STEPS.map((step, i) => {
          const done   = i <= current && status !== 'error';
          const active = i === current && status !== 'completed' && status !== 'error';
          return (
            <React.Fragment key={step}>
              <div className="flex flex-col items-center">
                <div className={`w-7 h-7 rounded-full flex items-center justify-center border-2 text-[10px] font-bold transition-all
                  ${done
                    ? 'bg-[var(--success)] border-[var(--success)] text-white'
                    : active
                    ? 'border-[var(--brand)] text-[var(--brand)] animate-pulse'
                    : status === 'error'
                    ? 'border-[var(--danger)] text-[var(--danger)]'
                    : 'border-[var(--border)] text-[var(--text-muted)]'}`}
                >
                  {done ? '✓' : i + 1}
                </div>
                <span className="text-[10px] text-[var(--text-muted)] mt-1 capitalize whitespace-nowrap">{step}</span>
              </div>
              {i < STATUS_STEPS.length - 1 && (
                <div className={`flex-1 h-0.5 mx-1 mt-3.5 w-8 sm:w-12 ${i < current ? 'bg-[var(--success)]' : 'bg-[var(--border)]'}`} />
              )}
            </React.Fragment>
          );
        })}
      </div>
    </div>
  );
}

// ── Page ──────────────────────────────────────────────────────────────────────

export default function DocumentDetailPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const [activeChunkIdx, setActiveChunkIdx] = useState<number | null>(null);
  const [viewerPage,     setViewerPage]     = useState(1);
  const [showViewer,     setShowViewer]     = useState(false);

  const { data: doc, isLoading, isError, refetch } = useQuery({
    queryKey: ['document', id],
    queryFn:  () => documentApi.getStatus(id),
    enabled:  !!id,
    refetchInterval: (q) => {
      const s = q.state.data?.status;
      return s && !['completed', 'error'].includes(s) ? 2000 : false;
    },
  });

  const { data: chunks = [] } = useQuery({
    queryKey: ['document-chunks', id],
    queryFn:  () => documentApi.getChunks(id),
    enabled:  doc?.status === 'completed',
  });

  if (isLoading) return <div className="max-w-5xl mx-auto space-y-4"><SkeletonCard lines={4} /></div>;
  if (isError || !doc) return <ErrorState title="Document not found" onRetry={() => refetch()} />;

  const progress     = PROGRESS_MAP[doc.status] ?? 0;
  const isProcessing = !['completed', 'error'].includes(doc.status);
  const activeChunk  = activeChunkIdx !== null ? chunks[activeChunkIdx] : null;
  const fileUrl      = documentFileUrl(doc.document_id);

  return (
    <div className="max-w-5xl mx-auto space-y-4 sm:space-y-6 pb-12">

      {/* Back */}
      <button
        onClick={() => router.back()}
        className="flex items-center gap-2 text-xs text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-colors"
      >
        <ArrowLeft className="w-4 h-4" /> Back to documents
      </button>

      {/* ── Document header ── */}
      <div className="bg-[var(--surface)] rounded-xl border border-[var(--border-strong)] p-4 sm:p-6 shadow-md space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-3">
          <div className="flex items-center gap-3 min-w-0">
            <div className="p-2.5 sm:p-3 rounded-lg bg-[var(--brand-subtle)] shrink-0">
              <FileText className="w-4 h-4 sm:w-5 sm:h-5 text-[var(--brand)]" />
            </div>
            <div className="min-w-0">
              <h1 className="text-base sm:text-lg font-bold text-[var(--text-primary)] truncate">
                {doc.filename}
              </h1>
              <div className="flex items-center gap-2 mt-1 flex-wrap">
                <Badge variant="outline">{doc.status}</Badge>
                {doc.chunk_count > 0 && (
                  <Badge variant="info">{doc.chunk_count} chunks extracted</Badge>
                )}
              </div>
            </div>
          </div>
          <div className="flex items-center gap-2 shrink-0">
            {doc.status === 'completed' && (
              <button
                onClick={() => setShowViewer(v => !v)}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-lg bg-[var(--brand)] text-white hover:opacity-90 transition-all"
              >
                <Eye className="w-3.5 h-3.5" />
                {showViewer ? 'Hide PDF' : 'View PDF'}
              </button>
            )}
            {isProcessing && <Loader2 className="w-5 h-5 text-[var(--brand)] animate-spin" />}
            {doc.status === 'completed' && <CheckCircle2 className="w-5 h-5 text-[var(--success)]" />}
            {doc.status === 'error'     && <AlertCircle  className="w-5 h-5 text-[var(--danger)]" />}
          </div>
        </div>

        {/* Progress bar */}
        <div className="space-y-1.5">
          <div className="flex justify-between text-xs text-[var(--text-secondary)]">
            <span>Processing progress</span>
            <span className="num-tabular font-bold text-[var(--text-primary)]">{progress}%</span>
          </div>
          <div className="h-2 bg-[var(--surface-subtle)] rounded-full overflow-hidden">
            <div
              className="h-full rounded-full transition-all duration-500"
              style={{
                width:      `${progress}%`,
                background: doc.status === 'error' ? 'var(--danger)' : 'var(--brand)',
              }}
            />
          </div>
        </div>

        {/* Timeline — scrolls on mobile */}
        <ProcessingTimeline status={doc.status} />

        {doc.error_message && (
          <div className="text-xs text-[var(--danger)] bg-[var(--danger-subtle)] p-3 rounded-lg border border-[var(--danger)]/30">
            {doc.error_message}
          </div>
        )}
      </div>

      {/* ── Split pane (stacks on mobile, side-by-side on lg when viewer open) ── */}
      {doc.status === 'completed' && (
        <div className={`grid gap-4 sm:gap-6 ${showViewer ? 'grid-cols-1 lg:grid-cols-2' : 'grid-cols-1'}`}>

          {/* PDF viewer */}
          {showViewer && (
            <div className="space-y-3">
              <h2 className="text-sm font-bold text-[var(--text-primary)]">PDF Viewer</h2>
              <DocumentViewer
                fileUrl={fileUrl}
                initialPage={viewerPage}
                highlightText={activeChunk?.content?.slice(0, 60)}
              />
            </div>
          )}

          {/* Extracted chunks */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <h2 className="text-sm font-bold text-[var(--text-primary)]">Extracted Text Chunks</h2>
              <Badge variant="info">{chunks.length} chunks</Badge>
            </div>

            {chunks.length === 0 ? (
              <EmptyState
                title="No chunks extracted"
                description="The document may still be processing."
                icon={FileText}
              />
            ) : (
              <div className="space-y-2 max-h-[500px] sm:max-h-[600px] overflow-y-auto pr-1">
                {chunks.map((chunk, idx) => (
                  <button
                    key={chunk.id}
                    onClick={() => {
                      setActiveChunkIdx(idx);
                      setViewerPage(chunk.page_number ?? 1);
                      setShowViewer(true);
                    }}
                    className={`w-full text-left transition-colors rounded-lg border ${
                      activeChunkIdx === idx
                        ? 'border-[var(--brand)] ring-1 ring-[var(--brand)]/30 bg-[var(--brand-subtle)]/20'
                        : 'border-[var(--border)] hover:border-[var(--brand)]/50 bg-[var(--surface)]'
                    }`}
                  >
                    <EvidenceHighlight
                      text={chunk.content}
                      highlight={activeChunkIdx === idx ? chunk.content.slice(0, 30) : undefined}
                      pageNumber={chunk.page_number}
                      relevanceScore={chunk.extraction_confidence ?? undefined}
                      chunkIndex={chunk.chunk_index}
                      sourceDocument={chunk.section_name ?? undefined}
                    />
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
