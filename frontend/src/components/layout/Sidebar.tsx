'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  LayoutDashboard,
  Users,
  FileText,
  Sliders,
  FileSpreadsheet,
  Settings,
  Layers,
  ShieldCheck,
  ChevronDown,
  ChevronUp,
  X,
} from 'lucide-react';
import { GlossaryTooltip } from '@/components/common/GlossaryTooltip';

interface NavGroup {
  label: string;
  items: {
    name: string;
    href: string;
    icon: React.ElementType;
  }[];
}

const navGroups: NavGroup[] = [
  {
    label: 'WORKSPACE',
    items: [
      { name: 'Overview', href: '/dashboard', icon: LayoutDashboard },
      { name: 'Suppliers', href: '/suppliers', icon: Users },
      { name: 'Scenarios', href: '/scenarios', icon: Sliders },
    ],
  },
  {
    label: 'EVIDENCE',
    items: [
      { name: 'Documents', href: '/documents', icon: FileText },
      { name: 'Verification', href: '/documents/verification', icon: ShieldCheck },
    ],
  },
  {
    label: 'OUTPUT',
    items: [
      { name: 'Reports', href: '/reports', icon: FileSpreadsheet },
    ],
  },
  {
    label: 'SYSTEM',
    items: [
      { name: 'Settings', href: '/settings', icon: Settings },
    ],
  },
];

interface SidebarProps {
  isOpen?: boolean;
  onClose?: () => void;
}

const SidebarContent: React.FC<{ onLinkClick?: () => void }> = ({ onLinkClick }) => {
  const pathname = usePathname();
  const [showTechDetails, setShowTechDetails] = useState(false);

  return (
    <>
      {/* Sectional Navigation Links */}
      <nav className="flex-1 px-3 py-4 space-y-6 overflow-y-auto" aria-label="Main navigation">
        {navGroups.map((group) => (
          <div key={group.label} className="space-y-1">
            <div className="px-3 text-[10px] font-bold text-textMuted tracking-wider uppercase mb-1.5">
              {group.label}
            </div>
            {group.items.map((item) => {
              const isActive = pathname === item.href || (item.href !== '/dashboard' && pathname.startsWith(item.href));
              const Icon = item.icon;
              return (
                <Link
                  key={item.name}
                  href={item.href}
                  aria-label={item.name}
                  aria-current={isActive ? 'page' : undefined}
                  onClick={onLinkClick}
                  className={`flex items-center justify-between px-3.5 py-2.5 text-xs font-medium rounded-xl transition-all duration-150 relative ${
                    isActive
                      ? 'bg-brandSubtle text-brand font-bold shadow-xs'
                      : 'text-textSecondary hover:text-textPrimary hover:bg-surfaceSubtle'
                  }`}
                >
                  <div className="flex items-center">
                    {isActive && (
                      <span className="absolute left-0 top-2 bottom-2 w-[3.5px] bg-brand rounded-r-full" />
                    )}
                    <Icon className={`w-4 h-4 mr-2.5 ${isActive ? 'text-brand' : 'text-textMuted'}`} />
                    <span>{item.name}</span>
                  </div>
                </Link>
              );
            })}
          </div>
        ))}
      </nav>

      {/* Docked Footer: "How this decision was made" */}
      <div className="p-3 mx-3 mb-4 rounded-xl bg-surfaceSubtle border border-borderDefault space-y-1.5 text-xs">
        <div className="flex items-center justify-between">
          <div className="font-bold text-textPrimary">How this decision was made</div>
          <span className="flex h-2 w-2 relative">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-success opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2 w-2 bg-success"></span>
          </span>
        </div>

        <p className="text-[11px] text-textSecondary leading-snug">
          100% evidence-grounded evaluation. Scores are mathematically calculated from ingested quotation PDFs.
        </p>

        <button
          onClick={() => setShowTechDetails(!showTechDetails)}
          className="text-[10px] font-mono text-brand hover:underline font-semibold flex items-center pt-1"
        >
          <span>Technical details</span>
          {showTechDetails ? (
            <ChevronUp className="w-3 h-3 ml-1" />
          ) : (
            <ChevronDown className="w-3 h-3 ml-1" />
          )}
        </button>

        {showTechDetails && (
          <div className="pt-2 border-t border-borderDefault text-[10px] font-mono text-textMuted space-y-1 bg-surface p-2 rounded border border-borderDefault">
            <div>• <GlossaryTooltip termKey="deterministic">Deterministic Engine</GlossaryTooltip></div>
            <div>• <GlossaryTooltip termKey="rag">RAG Vector Retrieval</GlossaryTooltip></div>
            <div>• <GlossaryTooltip termKey="chunk">Source Excerpts</GlossaryTooltip>: 10 Active</div>
          </div>
        )}
      </div>
    </>
  );
};

export const Sidebar: React.FC<SidebarProps> = ({ isOpen = false, onClose }) => {
  return (
    <>
      {/* ── Mobile Overlay ─────────────────────────────────────────── */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black/50 backdrop-blur-sm z-40 lg:hidden"
          onClick={onClose}
          aria-hidden="true"
        />
      )}

      {/* ── Mobile Drawer ──────────────────────────────────────────── */}
      <aside
        className={`
          fixed left-0 top-0 h-screen w-[280px] bg-[var(--surface)] text-[var(--text-primary)]
          flex flex-col border-r border-[var(--border)] z-50 select-none
          transition-transform duration-300 ease-in-out
          lg:translate-x-0
          ${isOpen ? 'translate-x-0' : '-translate-x-full'}
          lg:block
        `}
        aria-label="Sidebar navigation"
      >
        {/* Brand Header */}
        <div className="p-5 border-b border-[var(--border)] flex items-center justify-between shrink-0">
          <div className="flex items-center space-x-3">
            <img src="/logo.png" alt="Logo" className="w-8 h-8 object-contain" />
            <div>
              <h1 className="font-bold text-xs text-[var(--text-primary)] tracking-tight leading-none uppercase">
                Manufacturing
              </h1>
              <span className="text-xs text-[var(--brand)] font-semibold tracking-wide">
                Decision Copilot
              </span>
            </div>
          </div>
          {/* Close button — mobile only */}
          <button
            onClick={onClose}
            className="lg:hidden p-1.5 rounded-lg hover:bg-[var(--surface-subtle)] text-[var(--text-muted)] transition-colors"
            aria-label="Close sidebar"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        <SidebarContent onLinkClick={onClose} />
      </aside>
    </>
  );
};
