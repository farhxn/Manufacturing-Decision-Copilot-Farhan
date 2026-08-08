import { SkeletonCard } from '@/components/ui/Skeleton';
export default function ReportsLoading() {
  return (
    <div className="max-w-4xl mx-auto pt-4 space-y-4">
      <SkeletonCard lines={2} />
      <SkeletonCard lines={8} />
    </div>
  );
}
