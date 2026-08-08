import { SkeletonTable } from '@/components/ui/Skeleton';
export default function DocumentsLoading() {
  return <div className="max-w-5xl mx-auto pt-4"><SkeletonTable rows={4} /></div>;
}
