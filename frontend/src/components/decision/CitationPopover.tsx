'use client';

import React, { useState } from 'react';
import { FileText, CheckCircle2, ExternalLink } from 'lucide-react';
import Link from 'next/link';

interface CitationPopoverProps {
  claim: string;
  sourceDocument: string;
  pageNumber: number;
  chunkText: string;
  documentId?: string | null;
  verifiedDate?: string;
  children: React.ReactNode;
}

export const CitationPopover: React.FC<CitationPopoverProps> = ({
  claim,
  sourceDocument,
  pageNumber,
  chunkText,
  documentId,
  verifiedDate = 'Verified Today',
  children,
}) => {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div
      className="relative inline-block"
      onMouseEnter={() => setIsOpen(true)}
      onMouseLeave={() => setIsOpen(false)}
    >
      <span className="cursor-help underline decoration-dotted decoration-[#B86B3D] underline-offset-4">
        {children}
      </span>

      {isOpen && (
        <div className="absolute left-0 bottom-full mb-2 w-72 p-3 bg-[#171817] text-[#FBFAF7] rounded-xl border border-[#303230] shadow-2xl z-50 text-xs animate-entrance space-y-2">
          <div className="flex items-center justify-between border-b border-[#303230] pb-1.5">
            <div className="flex items-center space-x-1.5 text-[#557A68] font-bold text-[11px]">
              <CheckCircle2 className="w-3.5 h-3.5" />
              <span>Evidence Verified</span>
            </div>
            <span className="text-[10px] font-mono text-[#858780]">{verifiedDate}</span>
          </div>

          <div className="space-y-1">
            <div className="text-[10px] font-mono text-[#B86B3D] font-semibold flex items-center">
              <FileText className="w-3 h-3 mr-1" />
              {sourceDocument} (Page {pageNumber})
            </div>
            <p className="text-[11px] text-[#D8D5CC] italic bg-[#202120] p-2 rounded border border-[#303230] leading-snug">
              &ldquo;{chunkText}&rdquo;
            </p>
          </div>

          <div className="pt-1 flex items-center justify-between text-[10px] text-[#858780]">
            <span className="truncate mr-2">Claim: {claim}</span>
            <Link
              href={documentId ? `/documents/${documentId}?page=${pageNumber}` : "/documents"}
              target={documentId ? "_blank" : undefined}
              className="text-[#B86B3D] hover:underline font-semibold flex items-center shrink-0"
            >
              Open PDF <ExternalLink className="w-2.5 h-2.5 ml-1" />
            </Link>
          </div>
        </div>
      )}
    </div>
  );
};
