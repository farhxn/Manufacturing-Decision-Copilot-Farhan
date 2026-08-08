import React from 'react';
import { clsx } from 'clsx';

type BadgeVariant = 'default' | 'success' | 'warning' | 'danger' | 'info' | 'brand' | 'outline';

interface BadgeProps {
  children: React.ReactNode;
  variant?: BadgeVariant;
  className?: string;
}

const variantClasses: Record<BadgeVariant, string> = {
  default:  'bg-[var(--surface-subtle)] text-[var(--text-secondary)] border border-[var(--border)]',
  success:  'bg-[var(--success-subtle)] text-[var(--success)]',
  warning:  'bg-[var(--warning-subtle)] text-[var(--warning)]',
  danger:   'bg-[var(--danger-subtle)] text-[var(--danger)]',
  info:     'bg-[var(--info-subtle)] text-[var(--info)]',
  brand:    'bg-[var(--brand-subtle)] text-[var(--brand)]',
  outline:  'border border-[var(--border-strong)] text-[var(--text-secondary)]',
};

export function Badge({ children, variant = 'default', className }: BadgeProps) {
  return (
    <span
      className={clsx(
        'inline-flex items-center px-2 py-0.5 rounded text-[11px] font-semibold',
        variantClasses[variant],
        className,
      )}
    >
      {children}
    </span>
  );
}
