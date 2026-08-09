'use client';

import React, { useState } from 'react';
import { CheckCircle2, ChevronDown, ChevronRight, FileText, ShieldCheck, DollarSign, Clock, AlertCircle, Trophy } from 'lucide-react';

import type { RankedSupplier, Recommendation } from '@/types';
import { CitationPopover } from './CitationPopover';
import { getUniqueEvidenceCount } from '@/components/suppliers/EvidencePanel';

interface ReasoningPanelProps {
  isOpen: boolean;
  onClose: () => void;
  topSupplier?: RankedSupplier;
  recommendation?: Recommendation;
}

export const ReasoningPanel: React.FC<ReasoningPanelProps> = ({ 
  isOpen, 
  onClose, 
  topSupplier,
  recommendation
}) => {
  const [expandedStep, setExpandedStep] = useState<string | null>('01');

  if (!isOpen || !topSupplier || !recommendation) return null;

  const steps = [
    {
      step: '01',
      title: 'Eligibility & Mandatory Compliance',
      icon: ShieldCheck,
      status: 'Verified' as const,
      summary: `Score ${topSupplier.scores.compliance_score.toFixed(0)}/100 compliance requirements met.`,
      scoreContribution: `Factor Score: ${topSupplier.scores.compliance_score.toFixed(0)} / 100`,
      details: [
        {
          text: `Verified Compliance Score: ${topSupplier.scores.compliance_score.toFixed(0)}`,
          citation: topSupplier.citations?.compliance
        }
      ],
    },
    {
      step: '02',
      title: 'Commercial & Landed Cost Analysis',
      icon: DollarSign,
      status: 'Passed' as const,
      summary: `$${topSupplier.scores.landed_cost.toFixed(2)} landed cost per unit.`,
      scoreContribution: `Factor Score: ${topSupplier.scores.cost_score.toFixed(0)} / 100`,
      details: [
        {
          text: `Landed cost quoted at $${topSupplier.scores.landed_cost.toFixed(2)}`,
          citation: topSupplier.citations?.landed_cost
        },
        {
          text: `Competitive cost score: ${topSupplier.scores.cost_score.toFixed(0)} / 100`
        }
      ],
    },
    {
      step: '03',
      title: 'Delivery & Lead Time Assessment',
      icon: Clock,
      status: 'Passed' as const,
      summary: `${topSupplier.lead_time_days} days delivery lead time.`,
      scoreContribution: `Factor Score: ${topSupplier.scores.delivery_score.toFixed(0)} / 100`,
      details: [
        {
          text: `Quoted production/delivery time: ${topSupplier.lead_time_days} days`,
          citation: topSupplier.citations?.lead_time
        }
      ],
    },
    {
      step: '04',
      title: 'Risk Profile Evaluation',
      icon: AlertCircle,
      status: 'Verified' as const,
      summary: `Risk score of ${topSupplier.scores.risk_score.toFixed(1)}/100.`,
      scoreContribution: `Factor Score: ${topSupplier.scores.risk_score.toFixed(0)} / 100`,
      details: [
        {
          text: `Risk Assessment Score: ${topSupplier.scores.risk_score.toFixed(1)}`,
          citation: topSupplier.citations?.risk
        }
      ],
    },
    {
      step: '05',
      title: 'Evidence Attribution & AI Analysis',
      icon: FileText,
      status: 'Verified' as const,
      summary: `${getUniqueEvidenceCount(recommendation)} verified supporting evidence excerpts mapped.`,
      scoreContribution: `Confidence: ${(recommendation.confidence_score).toFixed(1)}%`,
      details: recommendation.pros.map((pro, idx) => ({
        text: pro,
        citation: recommendation.pros_citations?.[idx]
      })),
    },
  ];

  return (
    <div className="fixed inset-0 bg-surfaceInk/50 backdrop-blur-xs z-50 flex justify-end transition-opacity">
      <div className="bg-surface w-full max-w-xl h-full border-l border-borderDefault flex flex-col shadow-2xl overflow-hidden animate-entrance">
        {/* Panel Header */}
        <div className="p-6 border-b border-borderDefault flex items-center justify-between bg-surfaceSubtle">
          <div>
            <div className="text-[10px] font-bold text-brand uppercase tracking-wider">Causal Decision Resolution</div>
            <h3 className="text-lg font-bold text-textPrimary">Why {topSupplier.supplier_name}?</h3>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-textMuted hover:text-textPrimary hover:bg-surfaceTertiary transition-all"
          >
            ✕
          </button>
        </div>

        {/* Resolved Composite Score Box */}
        <div className="p-4 mx-6 mt-6 rounded-xl bg-surfaceInk text-surface border border-borderStrong flex items-center justify-between shadow-md">
          <div className="flex items-center space-x-3">
            <div className="p-2 rounded-lg bg-brandSubtle text-brand">
              <Trophy className="w-5 h-5" />
            </div>
            <div>
              <div className="text-xs font-bold text-surface">{topSupplier.supplier_name}</div>
              <div className="text-[10px] text-textMuted">Decision Score {topSupplier.final_score.toFixed(1)}</div>
            </div>
          </div>
          <div className="text-right">
            <div className="text-[10px] font-mono text-textMuted uppercase">Composite Score</div>
            <div className="text-2xl font-extrabold text-brand num-tabular">{topSupplier.final_score.toFixed(1)} / 100</div>
          </div>
        </div>

        {/* Steps List */}
        <div className="flex-1 overflow-y-auto p-6 space-y-4">
          {steps.map((item) => {
            const isExpanded = expandedStep === item.step;
            const Icon = item.icon;
            return (
              <div
                key={item.step}
                className="border border-borderDefault rounded-xl overflow-hidden bg-surface transition-all"
              >
                <button
                  onClick={() => setExpandedStep(isExpanded ? null : item.step)}
                  className="w-full p-4 text-left flex items-center justify-between bg-surface hover:bg-surfaceSubtle/50 transition-colors"
                >
                  <div className="flex items-center space-x-3">
                    <span className="text-xs font-mono font-bold text-brand">{item.step}</span>
                    <Icon className="w-4 h-4 text-textSecondary" />
                    <span className="text-xs font-bold text-textPrimary">{item.title}</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-successSubtle text-success">
                      {item.status}
                    </span>
                    {isExpanded ? (
                      <ChevronDown className="w-4 h-4 text-textMuted" />
                    ) : (
                      <ChevronRight className="w-4 h-4 text-textMuted" />
                    )}
                  </div>
                </button>

                {/* Contribution Sub-bar */}
                <div className="px-4 py-2 text-[11px] text-brand font-mono border-t border-divider bg-brandSubtle/40 flex justify-between">
                  <span>{item.summary}</span>
                  <span className="font-bold shrink-0 ml-2">{item.scoreContribution}</span>
                </div>

                {/* Expanded Details */}
                {isExpanded && (
                  <div className="px-4 pb-4 pt-2 bg-surface border-t border-divider">
                    <ul className="space-y-1.5 text-xs text-textPrimary">
                      {item.details.map((detail, idx) => (
                        <li key={idx} className="flex items-start">
                          <CheckCircle2 className="w-3.5 h-3.5 mr-2 text-success shrink-0 mt-0.5" />
                          {detail.citation ? (
                            <CitationPopover
                              claim={detail.text}
                              sourceDocument={detail.citation.source_document}
                              pageNumber={detail.citation.page_number}
                              chunkText={detail.citation.chunk_text}
                              documentId={detail.citation.document_id}
                            >
                              {detail.text}
                            </CitationPopover>
                          ) : (
                            <span>{detail.text}</span>
                          )}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            );
          })}
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-borderDefault bg-surfaceSubtle flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 text-xs font-semibold bg-surfaceInk text-surface rounded-lg hover:opacity-90 transition-all"
          >
            Done Inspecting
          </button>
        </div>
      </div>
    </div>
  );
};
