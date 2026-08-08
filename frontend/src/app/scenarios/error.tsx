'use client';
import { ErrorState } from '@/components/ui/ErrorState';
export default function ScenariosError({ reset }: { reset: () => void }) {
  return <ErrorState title="Scenario simulator unavailable" onRetry={reset} />;
}
