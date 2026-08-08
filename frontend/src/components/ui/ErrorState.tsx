import React from 'react';
import { AlertTriangle, RefreshCw } from 'lucide-react';

interface ErrorStateProps {
  title?: string;
  message?: string;
  onRetry?: () => void;
}

export function ErrorState({
  title = 'Something went wrong',
  message,
  onRetry,
}: ErrorStateProps) {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center space-y-4">
      <div className="p-4 rounded-full bg-[var(--danger-subtle)] border border-[var(--danger)]/30">
        <AlertTriangle className="w-8 h-8 text-[var(--danger)]" />
      </div>
      <div className="space-y-1">
        <h3 className="text-sm font-semibold text-[var(--text-primary)]">{title}</h3>
        {message && (
          <p className="text-xs text-[var(--text-secondary)] max-w-xs">{message}</p>
        )}
      </div>
      {onRetry && (
        <button
          onClick={onRetry}
          className="inline-flex items-center px-4 py-2 text-xs font-semibold rounded-lg
            bg-[var(--surface-ink)] text-[var(--surface)] hover:opacity-90 transition-all"
        >
          <RefreshCw className="w-3.5 h-3.5 mr-2" />
          Try again
        </button>
      )}
    </div>
  );
}
