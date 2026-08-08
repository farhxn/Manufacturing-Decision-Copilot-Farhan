'use client';

import React, { useRef, useState, useCallback } from 'react';
import Link from 'next/link';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import {
  Upload, FileText, CheckCircle2, AlertCircle, Loader2,
  RefreshCw, Trash2, ExternalLink, CloudUpload, Link as LinkIcon,
} from 'lucide-react';
import { documentApi } from '@/services/api/documentApi';
import { supplierApi } from '@/services/api/supplierApi';
import { Badge } from '@/components/ui/Badge';
import { SkeletonTable } from '@/components/ui/Skeleton';
import { ErrorState } from '@/components/ui/ErrorState';
import { EmptyState } from '@/components/ui/EmptyState';
import type { DocumentSummary } from '@/types';
import { getActiveWorkspaceId, useWorkspaceStore } from '@/store/workspaceStore';

const ACCEPTED = '.pdf,.docx,.xlsx';

function statusBadge(status: string) {
  if (status === 'completed') return <Badge variant="success">Completed</Badge>;
  if (status === 'error')     return <Badge variant="danger">Error</Badge>;
  if (status === 'uploaded')  return <Badge variant="outline">Queued</Badge>;
  return <Badge variant="info">{status}</Badge>;
}

function StatusIcon({ status }: { status: string }) {
  if (status === 'completed') return <CheckCircle2 className="w-3.5 h-3.5 text-[var(--success)] shrink-0" />;
  if (status === 'error')     return <AlertCircle  className="w-3.5 h-3.5 text-[var(--danger)] shrink-0" />;
  return <Loader2 className="w-3.5 h-3.5 text-[var(--info)] animate-spin shrink-0" />;
}

function formatBytes(b: number) {
  if (b < 1024)            return `${b} B`;
  if (b < 1024 * 1024)     return `${(b / 1024).toFixed(1)} KB`;
  return `${(b / (1024 * 1024)).toFixed(1)} MB`;
}

export default function DocumentsPage() {
  const qc       = useQueryClient();
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragging,  setDragging]  = useState(false);
  const [uploading, setUploading] = useState(false);

  const activeWorkspaceId = useWorkspaceStore(state => state.activeWorkspaceId);
  const currentProjectId  = activeWorkspaceId || getActiveWorkspaceId();

  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ['documents', currentProjectId],
    queryFn:  () => documentApi.list(currentProjectId, 1, 50),
    refetchInterval: (q) => {
      const docs: DocumentSummary[] = q.state.data?.data ?? [];
      return docs.some(d => !['completed', 'error'].includes(d.status)) ? 3000 : false;
    },
  });

  const { data: suppliersData } = useQuery({
    queryKey: ['suppliers_list_for_upload', currentProjectId],
    queryFn:  () => supplierApi.list({ project_id: currentProjectId || undefined, limit: 100 }),
  });

  const suppliersList = suppliersData?.data ?? [];
  const [selectedSupplierId, setSelectedSupplierId] = useState('');

  const deleteMutation = useMutation({
    mutationFn: (id: string) => documentApi.delete(id),
    onSuccess:  () => { qc.invalidateQueries({ queryKey: ['documents'] }); toast.success('Document deleted'); },
    onError:    () => toast.error('Delete failed'),
  });

  const handleFiles = useCallback(async (files: FileList | null) => {
    if (!files || files.length === 0) return;
    setUploading(true);
    let succeeded = 0;
    for (const file of Array.from(files)) {
      try {
        await documentApi.upload(file, currentProjectId, selectedSupplierId || undefined);
        succeeded++;
      } catch (e: unknown) {
        toast.error(`${file.name}: ${e instanceof Error ? e.message : 'Upload failed'}`);
      }
    }
    setUploading(false);
    if (succeeded > 0) {
      toast.success(`${succeeded} file(s) uploaded and queued for processing`);
      qc.invalidateQueries({ queryKey: ['documents'] });
    }
  }, [qc, selectedSupplierId, currentProjectId]);

  const onDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragging(false);
    handleFiles(e.dataTransfer.files);
  }, [handleFiles]);

  const documents: DocumentSummary[] = data?.data ?? [];

  return (
    <div className="max-w-5xl mx-auto space-y-4 sm:space-y-6 pb-12">

      {/* ── Page header ── */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <div>
          <h1 className="text-xl font-bold text-[var(--text-primary)]">Documents</h1>
          <p className="text-xs text-[var(--text-secondary)] mt-0.5">
            Upload PDFs, DOCX, or XLSX files for AI processing
          </p>
        </div>
        <button
          onClick={() => refetch()}
          className="self-start sm:self-auto inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-lg bg-[var(--surface)] border border-[var(--border)] hover:bg-[var(--surface-subtle)] transition-all"
        >
          <RefreshCw className="w-3.5 h-3.5" /> Refresh
        </button>
      </div>

      {/* ── Upload zone ── */}
      <div className="bg-[var(--surface)] p-4 sm:p-6 rounded-xl border border-[var(--border)] shadow-[var(--shadow-card)] space-y-4">

        {/* Supplier selector */}
        <div className="flex flex-col space-y-1.5">
          <label className="text-sm font-semibold text-[var(--text-primary)] inline-flex items-center gap-1.5">
            <LinkIcon className="w-4 h-4 text-[var(--text-muted)]" />
            Link to Supplier <span className="text-[var(--text-muted)] font-normal text-xs">(Optional)</span>
          </label>
          <select
            value={selectedSupplierId}
            onChange={e => setSelectedSupplierId(e.target.value)}
            className="w-full sm:max-w-sm px-3 py-2 text-sm bg-[var(--surface-subtle)] border border-[var(--border)] rounded-lg text-[var(--text-primary)] focus:outline-none focus:border-[var(--brand)] transition-colors"
          >
            <option value="">-- General / Project Level --</option>
            {suppliersList.map(s => (
              <option key={s.id} value={s.id}>{s.name}</option>
            ))}
          </select>
          <p className="text-xs text-[var(--text-muted)]">
            Quotes extracted from this document will be attributed to the selected supplier.
          </p>
        </div>

        {/* Drop zone */}
        <div
          onDragOver={e => { e.preventDefault(); setDragging(true); }}
          onDragLeave={() => setDragging(false)}
          onDrop={onDrop}
          onClick={() => inputRef.current?.click()}
          className={`border-2 border-dashed rounded-xl p-8 sm:p-10 flex flex-col items-center justify-center cursor-pointer transition-all gap-3
            ${dragging
              ? 'border-[var(--brand)] bg-[var(--brand-subtle)]'
              : 'border-[var(--border)] bg-[var(--surface)] hover:border-[var(--brand)] hover:bg-[var(--brand-subtle)]/40'
            }`}
        >
          <input ref={inputRef} type="file" accept={ACCEPTED} multiple className="hidden"
            onChange={e => handleFiles(e.target.files)} />
          {uploading
            ? <Loader2 className="w-8 h-8 sm:w-10 sm:h-10 text-[var(--brand)] animate-spin" />
            : <CloudUpload className="w-8 h-8 sm:w-10 sm:h-10 text-[var(--text-muted)]" />
          }
          <div className="text-sm font-semibold text-[var(--text-primary)] text-center">
            {uploading ? 'Uploading…' : 'Drop files here or click to browse'}
          </div>
          <div className="text-xs text-[var(--text-muted)]">PDF, DOCX, XLSX · Max 50 MB per file</div>
        </div>
      </div>

      {/* ── Document list ── */}
      {isLoading && <SkeletonTable rows={4} />}
      {isError   && <ErrorState onRetry={() => refetch()} />}
      {!isLoading && !isError && documents.length === 0 && (
        <EmptyState
          title="No documents yet"
          description="Upload a supplier quotation or certificate to get started."
          icon={FileText}
        />
      )}

      {!isLoading && documents.length > 0 && (
        <>
          {/* ── Mobile card view (sm:hidden) ── */}
          <div className="sm:hidden space-y-3">
            {documents.map(doc => {
              const linkedSupplier = suppliersList.find(s => s.id === doc.supplier_id);
              return (
                <div
                  key={doc.id}
                  className="bg-[var(--surface)] rounded-xl border border-[var(--border)] p-4 space-y-3 shadow-[var(--shadow-card)]"
                >
                  {/* Filename + status icon */}
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex items-center gap-2 min-w-0">
                      <StatusIcon status={doc.status} />
                      <span className="text-xs font-semibold text-[var(--text-primary)] truncate">
                        {doc.filename}
                      </span>
                    </div>
                    {statusBadge(doc.status)}
                  </div>

                  {/* Meta row */}
                  <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-[11px] text-[var(--text-muted)]">
                    <span className="uppercase font-mono">{doc.file_type}</span>
                    <span>·</span>
                    <span className="num-tabular">{formatBytes(doc.file_size_bytes)}</span>
                    {doc.chunk_count > 0 && (
                      <>
                        <span>·</span>
                        <span className="num-tabular">{doc.chunk_count} chunks</span>
                      </>
                    )}
                    <span>·</span>
                    <span>{new Date(doc.created_at).toLocaleDateString()}</span>
                  </div>

                  {/* Supplier tag if linked */}
                  {linkedSupplier && (
                    <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-md bg-[var(--brand-subtle)]/30 text-[var(--brand)] text-[11px] font-semibold">
                      <LinkIcon className="w-3 h-3" />
                      {linkedSupplier.name}
                    </span>
                  )}

                  {/* Actions */}
                  <div className="flex items-center justify-between pt-1 border-t border-[var(--divider)]">
                    <Link
                      href={`/documents/${doc.id}`}
                      className="text-[var(--brand)] text-xs font-semibold inline-flex items-center gap-1 hover:underline"
                    >
                      View <ExternalLink className="w-3 h-3" />
                    </Link>
                    <button
                      onClick={() => deleteMutation.mutate(doc.id)}
                      disabled={deleteMutation.isPending}
                      className="text-[var(--danger)] hover:opacity-70 transition-opacity p-1"
                      aria-label={`Delete ${doc.filename}`}
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>
              );
            })}
          </div>

          {/* ── Desktop table view (hidden sm:block) ── */}
          <div className="hidden sm:block bg-[var(--surface)] rounded-xl border border-[var(--border)] overflow-hidden shadow-[var(--shadow-card)]">
            <div className="px-5 py-3 bg-[var(--surface-subtle)] border-b border-[var(--border)] text-xs font-semibold text-[var(--text-secondary)]">
              {documents.length} document{documents.length !== 1 ? 's' : ''}
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-xs">
                <thead className="border-b border-[var(--divider)] text-[var(--text-secondary)]">
                  <tr>
                    <th className="py-3 px-4 text-left font-semibold">Filename</th>
                    <th className="py-3 px-4 text-left font-semibold">Type</th>
                    <th className="py-3 px-4 text-left font-semibold">Size</th>
                    <th className="py-3 px-4 text-left font-semibold">Linked Supplier</th>
                    <th className="py-3 px-4 text-left font-semibold">Status</th>
                    <th className="py-3 px-4 text-right font-semibold">Chunks</th>
                    <th className="py-3 px-4 text-left font-semibold">Uploaded</th>
                    <th className="py-3 px-4" />
                  </tr>
                </thead>
                <tbody className="divide-y divide-[var(--divider)]">
                  {documents.map(doc => (
                    <tr key={doc.id} className="hover:bg-[var(--surface-subtle)]/50 transition-colors">
                      <td className="py-3 px-4 font-medium text-[var(--text-primary)]">
                        <div className="flex items-center gap-2">
                          <StatusIcon status={doc.status} />
                          <span className="truncate max-w-[200px]">{doc.filename}</span>
                        </div>
                      </td>
                      <td className="py-3 px-4 text-[var(--text-secondary)] uppercase font-mono">{doc.file_type}</td>
                      <td className="py-3 px-4 text-[var(--text-secondary)] num-tabular">{formatBytes(doc.file_size_bytes)}</td>
                      <td className="py-3 px-4">
                        {doc.supplier_id ? (
                          <span className="inline-flex items-center gap-1.5 px-2 py-1 rounded-md bg-[var(--brand-subtle)]/30 text-[var(--brand)] text-[11px] font-semibold truncate max-w-[150px]">
                            <LinkIcon className="w-3 h-3 shrink-0" />
                            {suppliersList.find(s => s.id === doc.supplier_id)?.name || 'Linked'}
                          </span>
                        ) : (
                          <span className="text-[11px] text-[var(--text-muted)]">General</span>
                        )}
                      </td>
                      <td className="py-3 px-4">{statusBadge(doc.status)}</td>
                      <td className="py-3 px-4 text-right num-tabular text-[var(--text-secondary)]">{doc.chunk_count}</td>
                      <td className="py-3 px-4 text-[var(--text-muted)]">
                        {new Date(doc.created_at).toLocaleDateString()}
                      </td>
                      <td className="py-3 px-4">
                        <div className="flex items-center justify-end gap-2">
                          <Link
                            href={`/documents/${doc.id}`}
                            className="text-[var(--brand)] hover:underline inline-flex items-center gap-1"
                          >
                            View <ExternalLink className="w-3 h-3" />
                          </Link>
                          <button
                            onClick={() => deleteMutation.mutate(doc.id)}
                            disabled={deleteMutation.isPending}
                            className="text-[var(--danger)] hover:opacity-70 transition-opacity"
                            aria-label={`Delete ${doc.filename}`}
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                          </button>
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
    </div>
  );
}
