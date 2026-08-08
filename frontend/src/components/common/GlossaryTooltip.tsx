'use client';

import React, { useState } from 'react';
import { HelpCircle } from 'lucide-react';
import glossaryData from '@/lib/glossary.json';

type GlossaryKey = keyof typeof glossaryData;

interface GlossaryTooltipProps {
  termKey: GlossaryKey;
  children?: React.ReactNode;
}

export const GlossaryTooltip: React.FC<GlossaryTooltipProps> = ({ termKey, children }) => {
  const [isOpen, setIsOpen] = useState(false);
  const entry = glossaryData[termKey];

  if (!entry) return <>{children}</>;

  return (
    <span
      className="relative inline-flex items-center"
      onMouseEnter={() => setIsOpen(true)}
      onMouseLeave={() => setIsOpen(false)}
    >
      <span>{children || entry.plainLabel}</span>
      <HelpCircle className="w-3 h-3 ml-1 text-textMuted hover:text-brand cursor-help shrink-0" />

      {isOpen && (
        <span className="absolute left-0 bottom-full mb-1.5 w-64 p-3 bg-surfaceInk text-textPrimary rounded-xl border border-borderStrong shadow-xl z-50 text-xs space-y-1 block pointer-events-none">
          <span className="font-bold text-brand block text-[11px] font-mono uppercase tracking-wider">
            {entry.plainLabel} ({entry.term})
          </span>
          <span className="text-textSecondary text-[11px] leading-relaxed block font-normal">
            {entry.tooltip}
          </span>
        </span>
      )}
    </span>
  );
};
