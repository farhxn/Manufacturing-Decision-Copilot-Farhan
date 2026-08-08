import { SkeletonTable } from '@/components/ui/Skeleton';
export default function SuppliersLoading() {
  return <div className="max-w-7xl mx-auto pt-4"><SkeletonTable rows={6} /></div>;
}
