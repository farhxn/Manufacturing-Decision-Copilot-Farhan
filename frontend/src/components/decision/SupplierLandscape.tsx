'use client';

import React from 'react';
import Link from 'next/link';
import { ExternalLink } from 'lucide-react';
import { CitationPopover } from '@/components/decision/CitationPopover';

export interface SupplierData {
  id?: string;
  rank: number;
  name: string;
  country: string;
  landedCost: string;
  leadTime: string;
  risk: 'Low' | 'Medium' | 'High';
  compliance: string;
  score: number;
  status: 'Recommended' | 'Eligible' | 'Disqualified';
  citations?: Record<string, { document_id?: string | null, source_document: string, page_number: number, chunk_text: string }>;
}

export const defaultSuppliers: SupplierData[] = [
  {
    id: 'acme-precision-mfg',
    rank: 1,
    name: 'Acme Precision Mfg',
    country: 'Germany',
    landedCost: '$145.00',
    leadTime: '14 days',
    risk: 'Low',
    compliance: 'ISO 9001, AS9100D',
    score: 88.5,
    status: 'Recommended',
  },
  {
    id: 'techforge-industries',
    rank: 2,
    name: 'TechForge Industries',
    country: 'Taiwan',
    landedCost: '$118.00',
    leadTime: '21 days',
    risk: 'Low',
    compliance: 'ISO 9001, RoHS',
    score: 84.2,
    status: 'Eligible',
  },
  {
    id: 'fasttrack-manufacturing',
    rank: 3,
    name: 'FastTrack Manufacturing',
    country: 'Mexico',
    landedCost: '$110.00',
    leadTime: '10 days',
    risk: 'Medium',
    compliance: 'ISO 9001',
    score: 81.0,
    status: 'Eligible',
  },
  {
    id: 'reliable-parts-co',
    rank: 4,
    name: 'Reliable Parts Co',
    country: 'India',
    landedCost: '$102.00',
    leadTime: '18 days',
    risk: 'Medium',
    compliance: 'ISO 9001',
    score: 79.4,
    status: 'Eligible',
  },
  {
    id: 'global-fabrication-ltd',
    rank: 5,
    name: 'Global Fabrication Ltd',
    country: 'China',
    landedCost: '$89.00',
    leadTime: '28 days',
    risk: 'High',
    compliance: 'ISO 9001',
    score: 72.8,
    status: 'Eligible',
  },
];

export const SupplierLandscape: React.FC<{ suppliers?: SupplierData[] }> = ({
  suppliers = [],
}) => {
  return (
    <div className="space-y-6 select-none">
      {/* Overview First: Visual Score Comparison Bars */}
      <div className="bg-surface p-5 rounded-xl border border-borderDefault shadow-card space-y-4">
        <div className="flex items-center justify-between border-b border-borderDefault pb-3">
          <div>
            <span className="text-[10px] font-bold text-textMuted uppercase tracking-wider">Overview First</span>
            <h4 className="text-sm font-bold text-textPrimary">Supplier Composite Score Comparison</h4>
          </div>
          <span className="text-xs text-textSecondary font-mono">
            {suppliers.length} Vendor{suppliers.length !== 1 ? 's' : ''} Evaluated
          </span>
        </div>

        <div className="space-y-3">
          {suppliers.length === 0 ? (
            <div className="text-center text-textSecondary text-xs py-4">
              No suppliers available to display composite scores.
            </div>
          ) : (
            suppliers.map((s, i) => (
              <div key={s.id || `${s.name}-${i}`} className="flex items-center gap-2 sm:gap-4 text-xs">
                <div className="w-28 sm:w-48 truncate font-medium text-textPrimary flex items-center shrink-0">
                  <span className="font-mono text-textMuted text-[11px] mr-2 w-4 shrink-0">#{s.rank}</span>
                  <span className="truncate">{s.name}</span>
                </div>
                <div className="flex-1 bg-surfaceSubtle h-2.5 rounded-full overflow-hidden min-w-0">
                  <div
                    className={`h-full rounded-full transition-all duration-300 ${
                      s.rank === 1
                        ? 'bg-brand'
                        : s.risk === 'Low'
                        ? 'bg-textPrimary'
                        : s.risk === 'Medium'
                        ? 'bg-warning'
                        : 'bg-danger'
                    }`}
                    style={{ width: `${s.score}%` }}
                  />
                </div>
                <div className="w-10 sm:w-12 text-right font-bold num-tabular text-textPrimary shrink-0">
                  {s.score.toFixed(1)}
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Details Second: High-Density Table */}
      <div className="bg-surface rounded-xl border border-borderDefault shadow-card overflow-hidden">
        <div className="px-5 py-4 border-b border-borderDefault flex items-center justify-between">
          <div>
            <h4 className="text-sm font-bold text-textPrimary">Comparative Evaluation Details</h4>
            <p className="text-xs text-textSecondary">Ingested vendor bids and verified certs</p>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="bg-surfaceSubtle border-b border-borderDefault text-textSecondary font-semibold">
                <th className="py-3 px-4 w-10 text-center">Rank</th>
                <th className="py-3 px-4">Supplier Name</th>
                <th className="py-3 px-4">Country</th>
                <th className="py-3 px-4 text-right">Landed Cost</th>
                <th className="py-3 px-4 text-right">Lead Time</th>
                <th className="py-3 px-4 text-center">Risk Level</th>
                <th className="py-3 px-4">Compliance Certs</th>
                <th className="py-3 px-4 text-right">Score</th>
                <th className="py-3 px-4 text-center">Inspect</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-divider text-textPrimary">
              {suppliers.length === 0 ? (
                <tr>
                  <td colSpan={9} className="py-8 text-center text-textSecondary text-xs">
                    No suppliers available. Please add suppliers to the workspace.
                  </td>
                </tr>
              ) : (
                suppliers.map((s, i) => (
                  <tr
                    key={s.id || `${s.name}-${i}`}
                    className={`hover:bg-surfaceSubtle/60 transition-colors ${
                      s.rank === 1 ? 'bg-brandSubtle/30 font-medium' : ''
                    }`}
                  >
                    <td className="py-3 px-4 text-center font-bold num-tabular text-textSecondary">
                      #{s.rank}
                    </td>
                    <td className="py-3 px-4 font-semibold text-textPrimary flex items-center">
                      {s.rank === 1 && (
                        <span className="w-2 h-2 rounded-full bg-brand mr-2" />
                      )}
                      {s.name}
                    </td>
                    <td className="py-3 px-4 text-textSecondary">{s.country}</td>
                    <td className="py-3 px-4 text-right num-tabular font-medium">
                      <CitationPopover
                        claim={`Landed Cost is ${s.landedCost}`}
                        documentId={s.citations?.landed_cost?.document_id}
                        sourceDocument={s.citations?.landed_cost?.source_document || `${s.name} Pricing Proposal.pdf`}
                        pageNumber={s.citations?.landed_cost?.page_number || 2}
                        chunkText={s.citations?.landed_cost?.chunk_text || `The final landed cost per unit, including shipping and tariffs, is calculated at ${s.landedCost}.`}
                      >
                        {s.landedCost}
                      </CitationPopover>
                    </td>
                    <td className="py-3 px-4 text-right num-tabular text-textSecondary">
                      <CitationPopover
                        claim={`Lead Time is ${s.leadTime}`}
                        documentId={s.citations?.lead_time?.document_id}
                        sourceDocument={s.citations?.lead_time?.source_document || `${s.name} Operations SLA.pdf`}
                        pageNumber={s.citations?.lead_time?.page_number || 4}
                        chunkText={s.citations?.lead_time?.chunk_text || `We commit to a standard production lead time of ${s.leadTime} for the specified volumes.`}
                      >
                        {s.leadTime}
                      </CitationPopover>
                    </td>
                    <td className="py-3 px-4 text-center">
                      {s.risk === 'Low' && (
                        <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-successSubtle text-success">
                          Low
                        </span>
                      )}
                      {s.risk === 'Medium' && (
                        <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-warningSubtle text-warning">
                          Medium
                        </span>
                      )}
                      {s.risk === 'High' && (
                        <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-dangerSubtle text-danger">
                          High
                        </span>
                      )}
                    </td>
                    <td className="py-3 px-4 text-textSecondary">
                      <CitationPopover
                        claim={`Compliance is ${s.compliance}`}
                        documentId={s.citations?.compliance?.document_id}
                        sourceDocument={s.citations?.compliance?.source_document || `${s.name} Quality Certifications.pdf`}
                        pageNumber={s.citations?.compliance?.page_number || 1}
                        chunkText={s.citations?.compliance?.chunk_text || `The management system of ${s.name} has been audited and found to conform to the requirements of ${s.compliance}.`}
                      >
                        {s.compliance}
                      </CitationPopover>
                    </td>
                    <td className="py-3 px-4 text-right font-bold num-tabular text-textPrimary">
                      {s.score.toFixed(1)}
                    </td>
                    <td className="py-3 px-4 text-center">
                      <Link
                        href={`/suppliers/${s.id ?? s.rank}`}
                        className="text-brand hover:text-brand-hover font-semibold inline-flex items-center"
                      >
                        Inspect <ExternalLink className="w-3 h-3 ml-1" />
                      </Link>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
