'use client';
import { ErrorState } from '@/components/ui/ErrorState';
export default function ReportsError({ reset }: { reset: () => void }) {
  return <ErrorState title="Report unavailable" onRetry={reset} />;
}
