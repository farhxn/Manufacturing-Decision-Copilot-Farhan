'use client';

import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { ArrowLeft, CheckCircle2, ShieldCheck, FileText, Eye } from 'lucide-react';
import { documentApi } from '@/services/api/documentApi';
import { DocumentViewer } from '@/components/documents/DocumentViewer';
import { EvidenceHighlight } from '@/components/documents/EvidenceHighlight';
import { Badge } from '@/components/ui/Badge';
import { SkeletonCard } from '@/components/ui/Skeleton';
import { ErrorState } from '@/components/ui/ErrorState';
import { EmptyState } from '@/components/ui/EmptyState';
import { useRouter } from 'next/navigation';
import type { DocumentChunkWithMeta } from '@/types';

function documentFileUrl(documentId: string): string {
  const base = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000/api/v1';
  return `${base.replace(/\/$/, '')}/documents/${documentId}/file`;
}

export default function VerificationPage() {
  const router = useRouter();
  const [activeChunkIdx, setActiveChunkIdx] = useState<number | null>(null);
  const [viewerPage, setViewerPage] = useState(1);
  const [showViewer, setShowViewer] = useState(true); // default true on desktop

  const { data: chunks = [], isLoading, isError, refetch } = useQuery({
    queryKey: ['verification-queue'],
    queryFn: () => documentApi.getVerificationQueue(),
  });

  if (isLoading) return <div className="max-w-5xl mx-auto space-y-4"><SkeletonCard lines={6} /></div>;
  if (isError) return <ErrorState title="Failed to load queue" onRetry={() => refetch()} />;

  const activeChunk: DocumentChunkWithMeta | null = activeChunkIdx !== null ? chunks[activeChunkIdx] : null;
  const fileUrl = activeChunk ? documentFileUrl(activeChunk.document_id) : undefined;

  return (
    <div className="max-w-6xl mx-auto space-y-4 sm:space-y-6 pb-12">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <button
            onClick={() => router.back()}
            className="flex items-center gap-2 text-xs text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-colors mb-2"
          >
            <ArrowLeft className="w-4 h-4" /> Back
          </button>
          <div className="flex items-center gap-3">
            <div className="p-3 rounded-xl bg-[var(--brand-subtle)]">
              <ShieldCheck className="w-6 h-6 text-[var(--brand)]" />
            </div>
            <div>
              <h1 className="text-xl sm:text-2xl font-bold text-[var(--text-primary)] tracking-tight">
                Evidence Verification
              </h1>
              <p className="text-sm text-[var(--text-secondary)]">
                Review low-confidence extracted claims against original documents
              </p>
            </div>
          </div>
        </div>
        <div className="hidden sm:flex">
          <Badge variant="warning">{chunks.length} claims need review</Badge>
        </div>
      </div>

      <div className={`grid gap-4 sm:gap-6 ${showViewer && activeChunk ? 'grid-cols-1 lg:grid-cols-12' : 'grid-cols-1'}`}>
        
        {/* Extracted chunks list */}
        <div className={showViewer && activeChunk ? 'lg:col-span-5' : 'col-span-1'}>
          <div className="bg-[var(--surface)] border border-[var(--border)] rounded-xl shadow-sm p-4 space-y-4 flex flex-col h-[calc(100vh-200px)]">
            <div className="flex items-center justify-between pb-2 border-b border-[var(--border)] shrink-0">
              <h2 className="text-sm font-bold text-[var(--text-primary)]">Claims Queue</h2>
              <Badge variant="info">{chunks.length} pending</Badge>
            </div>

            {chunks.length === 0 ? (
              <EmptyState
                title="No claims to verify"
                description="All documents have high-confidence extractions."
                icon={CheckCircle2}
              />
            ) : (
              <div className="space-y-2 overflow-y-auto pr-1 flex-1">
                {chunks.map((chunk, idx) => (
                  <button
                    key={chunk.id}
                    onClick={() => {
                      setActiveChunkIdx(idx);
                      setViewerPage(chunk.page_number ?? 1);
                      setShowViewer(true);
                    }}
                    className={`w-full text-left transition-colors rounded-lg border p-1 ${
                      activeChunkIdx === idx
                        ? 'border-[var(--brand)] ring-1 ring-[var(--brand)]/30 bg-[var(--brand-subtle)]/20'
                        : 'border-[var(--border)] hover:border-[var(--brand)]/50 bg-[var(--surface)]'
                    }`}
                  >
                    <div className="px-3 pt-2 text-xs font-semibold text-[var(--text-secondary)] truncate flex items-center gap-1">
                      <FileText className="w-3 h-3" />
                      {chunk.document_filename}
                    </div>
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

        {/* PDF viewer */}
        {showViewer && activeChunk && fileUrl && (
          <div className="lg:col-span-7 bg-[var(--surface)] border border-[var(--border)] rounded-xl shadow-sm p-4 space-y-4 flex flex-col h-[calc(100vh-200px)]">
            <div className="flex items-center justify-between shrink-0">
              <h2 className="text-sm font-bold text-[var(--text-primary)] truncate max-w-[70%]">
                {activeChunk.document_filename} - Page {activeChunk.page_number}
              </h2>
              <button
                onClick={() => setShowViewer(false)}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-lg bg-[var(--surface-subtle)] hover:bg-[var(--border)] transition-all"
              >
                Hide PDF
              </button>
            </div>
            <div className="flex-1 min-h-0 border border-[var(--border)] rounded-lg overflow-hidden relative">
              <DocumentViewer
                fileUrl={fileUrl}
                initialPage={viewerPage}
                highlightText={activeChunk.content.slice(0, 60)}
              />
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
