'use client';
import { ErrorState } from '@/components/ui/ErrorState';
export default function SuppliersError({ reset }: { reset: () => void }) {
  return <ErrorState title="Could not load suppliers" onRetry={reset} />;
}
