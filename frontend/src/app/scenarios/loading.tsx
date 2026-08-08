import { SkeletonCard } from '@/components/ui/Skeleton';
export default function ScenariosLoading() {
  return (
    <div className="max-w-6xl mx-auto pt-4 grid grid-cols-1 lg:grid-cols-3 gap-6">
      <SkeletonCard lines={6} />
      <div className="lg:col-span-2 space-y-4">
        <SkeletonCard lines={3} />
        <SkeletonCard lines={3} />
      </div>
    </div>
  );
}
