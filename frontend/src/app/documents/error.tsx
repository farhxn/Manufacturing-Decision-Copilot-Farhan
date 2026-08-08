'use client';
import { ErrorState } from '@/components/ui/ErrorState';
export default function DocumentsError({ reset }: { reset: () => void }) {
  return <ErrorState title="Could not load documents" onRetry={reset} />;
}
