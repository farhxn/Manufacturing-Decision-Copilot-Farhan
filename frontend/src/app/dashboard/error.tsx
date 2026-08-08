'use client';
import { ErrorState } from '@/components/ui/ErrorState';
export default function DashboardError({ reset }: { reset: () => void }) {
  return <ErrorState title="Dashboard failed to load" onRetry={reset} />;
}
