'use client';

/**
 * DocumentViewer — PDF.js canvas renderer.
 *
 * Renders a single PDF page on a <canvas>. Jumps to `initialPage` on mount
 * and exposes prev/next navigation. Integrates with EvidenceHighlight by
 * accepting a `highlightText` prop — the matched snippet is drawn as a
 * yellow overlay after the page renders.
 *
 * Dynamically imports pdfjs-dist so the ~3 MB worker bundle never blocks
 * the initial page load.
 */

import React, { useCallback, useEffect, useRef, useState } from 'react';
import { ChevronLeft, ChevronRight, ZoomIn, ZoomOut, Loader2, AlertTriangle } from 'lucide-react';

interface DocumentViewerProps {
  /**
   * Full URL of the PDF to load — should point to
   * GET /api/v1/documents/{id}/file on the backend.
   */
  fileUrl: string;
  /** Page to jump to on initial render (1-indexed) */
  initialPage?: number;
  /** Text snippet to highlight on the rendered page */
  highlightText?: string;
  className?: string;
}

type PDFDocProxy = {
  numPages: number;
  getPage: (n: number) => Promise<PDFPageProxy>;
  destroy: () => void;
};

type PDFPageProxy = {
  getViewport: (opts: { scale: number }) => { width: number; height: number };
  render: (ctx: object) => { promise: Promise<void> };
  getTextContent: () => Promise<{ items: Array<{ str: string; transform: number[] }> }>;
};

const SCALE_STEP = 0.25;
const MIN_SCALE  = 0.5;
const MAX_SCALE  = 3.0;

export function DocumentViewer({
  fileUrl,
  initialPage = 1,
  highlightText,
  className = '',
}: DocumentViewerProps) {
  const canvasRef   = useRef<HTMLCanvasElement>(null);
  const overlayRef  = useRef<HTMLCanvasElement>(null);

  const [pdfDoc,      setPdfDoc]      = useState<PDFDocProxy | null>(null);
  const [pageNum,     setPageNum]     = useState(initialPage);
  const [numPages,    setNumPages]    = useState(0);
  const [scale,       setScale]       = useState(1.25);
  const [loading,     setLoading]     = useState(true);
  const [renderBusy,  setRenderBusy]  = useState(false);
  const [error,       setError]       = useState<string | null>(null);

  // ── Load PDF ────────────────────────────────────────────────────────────────
  useEffect(() => {
    if (!fileUrl) return;
    let cancelled = false;

    async function load() {
      setLoading(true);
      setError(null);
      try {
        // Dynamic import — keeps the 3 MB worker out of the initial bundle
        const pdfjsLib = await import('pdfjs-dist');
        // Point at the worker bundled with pdfjs-dist
        pdfjsLib.GlobalWorkerOptions.workerSrc = new URL(
          'pdfjs-dist/build/pdf.worker.min.mjs',
          import.meta.url,
        ).toString();

        const doc = await pdfjsLib.getDocument(fileUrl).promise;
        if (cancelled) { doc.destroy(); return; }
        setPdfDoc(doc as unknown as PDFDocProxy);
        setNumPages(doc.numPages);
        setPageNum(Math.min(initialPage, doc.numPages));
      } catch (e) {
        if (!cancelled) setError('Could not load PDF. Check the file URL or network connection.');
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    load();
    return () => { cancelled = true; };
  }, [fileUrl, initialPage]);

  // ── Render page ─────────────────────────────────────────────────────────────
  const renderPage = useCallback(async (doc: PDFDocProxy, num: number, sc: number) => {
    if (!canvasRef.current || !overlayRef.current) return;
    setRenderBusy(true);
    try {
      const page     = await doc.getPage(num);
      const viewport = page.getViewport({ scale: sc });

      const canvas = canvasRef.current;
      const ctx    = canvas.getContext('2d')!;
      canvas.width  = viewport.width;
      canvas.height = viewport.height;

      await page.render({ canvasContext: ctx, viewport }).promise;

      // Sync overlay canvas size
      const overlay = overlayRef.current;
      overlay.width  = viewport.width;
      overlay.height = viewport.height;

      // Draw highlight if text provided
      if (highlightText) {
        await drawHighlight(page, viewport, overlay, highlightText);
      }
    } finally {
      setRenderBusy(false);
    }
  }, [highlightText]);

  useEffect(() => {
    if (pdfDoc) renderPage(pdfDoc, pageNum, scale);
  }, [pdfDoc, pageNum, scale, renderPage]);

  // ── Highlight drawing ───────────────────────────────────────────────────────
  async function drawHighlight(
    page: PDFPageProxy,
    viewport: { width: number; height: number },
    overlay: HTMLCanvasElement,
    needle: string,
  ) {
    const ctx = overlay.getContext('2d')!;
    ctx.clearRect(0, 0, overlay.width, overlay.height);

    try {
      const textContent = await page.getTextContent();
      const needleLower = needle.toLowerCase().slice(0, 80); // cap for safety

      for (const item of textContent.items as Array<{ str: string; transform: number[] }>) {
        if (!item.str.toLowerCase().includes(needleLower.split(' ')[0])) continue;

        // transform = [scaleX, 0, 0, scaleY, tx, ty] (PDF coordinates)
        const [, , , scaleY, tx, ty] = item.transform;
        const canvasX = tx * (viewport.width / (overlay.width / ((viewport as any).scale ?? 1)));
        const canvasY = overlay.height - ty * ((viewport as any).scale ?? 1.25);
        const charW   = Math.abs(scaleY) * ((viewport as any).scale ?? 1.25);
        const w       = item.str.length * charW * 0.55;
        const h       = charW * 1.1;

        ctx.fillStyle   = 'rgba(253, 224, 71, 0.45)'; // yellow-300
        ctx.strokeStyle = 'rgba(234, 179, 8, 0.7)';   // yellow-500
        ctx.lineWidth   = 1;
        ctx.fillRect(canvasX, canvasY - h, w, h);
        ctx.strokeRect(canvasX, canvasY - h, w, h);
      }
    } catch {
      // Text layer unavailable — skip highlighting silently
    }
  }

  // ── Navigation ──────────────────────────────────────────────────────────────
  const goTo = (n: number) => setPageNum(Math.max(1, Math.min(n, numPages)));

  // ── Render ──────────────────────────────────────────────────────────────────
  if (loading) {
    return (
      <div className={`flex items-center justify-center h-96 rounded-xl border border-[var(--border)] bg-[var(--surface-subtle)] ${className}`}>
        <div className="flex flex-col items-center gap-3">
          <Loader2 className="w-8 h-8 text-[var(--brand)] animate-spin" />
          <span className="text-xs text-[var(--text-muted)]">Loading PDF…</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={`flex items-center justify-center h-48 rounded-xl border border-[var(--danger)]/30 bg-[var(--danger-subtle)] ${className}`}>
        <div className="flex flex-col items-center gap-2 text-center px-6">
          <AlertTriangle className="w-6 h-6 text-[var(--danger)]" />
          <p className="text-xs text-[var(--danger)]">{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className={`flex flex-col ${className}`}>
      {/* Toolbar */}
      <div className="flex items-center justify-between px-3 py-2 bg-[var(--surface-subtle)] border border-[var(--border)] rounded-t-xl text-xs">
        {/* Page navigation */}
        <div className="flex items-center gap-1">
          <button
            onClick={() => goTo(pageNum - 1)}
            disabled={pageNum <= 1 || renderBusy}
            className="p-1.5 rounded-lg hover:bg-[var(--surface)] disabled:opacity-40 transition-colors"
            aria-label="Previous page"
          >
            <ChevronLeft className="w-3.5 h-3.5" />
          </button>
          <span className="px-2 font-mono text-[var(--text-secondary)] select-none">
            {pageNum} / {numPages}
          </span>
          <button
            onClick={() => goTo(pageNum + 1)}
            disabled={pageNum >= numPages || renderBusy}
            className="p-1.5 rounded-lg hover:bg-[var(--surface)] disabled:opacity-40 transition-colors"
            aria-label="Next page"
          >
            <ChevronRight className="w-3.5 h-3.5" />
          </button>
        </div>

        {/* Zoom controls */}
        <div className="flex items-center gap-1">
          {renderBusy && <Loader2 className="w-3.5 h-3.5 text-[var(--brand)] animate-spin mr-1" />}
          <button
            onClick={() => setScale(s => Math.max(MIN_SCALE, +(s - SCALE_STEP).toFixed(2)))}
            disabled={scale <= MIN_SCALE || renderBusy}
            className="p-1.5 rounded-lg hover:bg-[var(--surface)] disabled:opacity-40 transition-colors"
            aria-label="Zoom out"
          >
            <ZoomOut className="w-3.5 h-3.5" />
          </button>
          <span className="w-12 text-center font-mono text-[var(--text-secondary)] select-none">
            {Math.round(scale * 100)}%
          </span>
          <button
            onClick={() => setScale(s => Math.min(MAX_SCALE, +(s + SCALE_STEP).toFixed(2)))}
            disabled={scale >= MAX_SCALE || renderBusy}
            className="p-1.5 rounded-lg hover:bg-[var(--surface)] disabled:opacity-40 transition-colors"
            aria-label="Zoom in"
          >
            <ZoomIn className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Canvas area */}
      <div className="relative overflow-auto border border-t-0 border-[var(--border)] rounded-b-xl bg-[var(--surface-subtle)] max-h-[640px]">
        <div className="relative inline-block m-4">
          {/* PDF render canvas */}
          <canvas ref={canvasRef} className="block shadow-md rounded" />
          {/* Highlight overlay — positioned absolute on top */}
          <canvas
            ref={overlayRef}
            className="absolute inset-0 pointer-events-none rounded"
          />
        </div>
      </div>
    </div>
  );
}
