'use client';

import React from 'react';
import { GlossaryTooltip } from '@/components/common/GlossaryTooltip';

interface FactorContribution {
  name: string;
  score: number;
  weight: string;
  contribution: string;
}

export interface ScoreBreakdownData {
  cost_score: number;
  quality_score: number;
  delivery_score: number;
  risk_score: number;
  compliance_score: number;
}

export const ScoreBreakdown: React.FC<{
  compositeScore: number;
  scores?: ScoreBreakdownData;
}> = ({ compositeScore, scores }) => {
  const factors = scores ? [
    { name: 'Compliance', score: scores.compliance_score, weight: '10%', contribution: 'Regulatory and standards alignment' },
    { name: 'Risk Profile', score: scores.risk_score, weight: '15%', contribution: 'Composite of financial and geo-risk' },
    { name: 'Delivery Lead Time', score: scores.delivery_score, weight: '15%', contribution: 'Derived from lead time commitments' },
    { name: 'Quality Certs', score: scores.quality_score, weight: '20%', contribution: 'Based on verified certificates' },
    { name: 'Landed Cost', score: scores.cost_score, weight: '30%', contribution: 'Calculated from unit price and landed cost' },
  ] : [];

  return (
    <div className="space-y-4 pt-1 select-none">
      {/* Header Row with minimum 16px gap to prevent text collision */}
      <div className="flex items-center justify-between text-xs border-b border-borderDefault pb-2 gap-4">
        <span className="font-bold text-textPrimary shrink-0">
          <GlossaryTooltip termKey="compositeScore">Score Breakdown</GlossaryTooltip>
        </span>
        <span className="num-tabular font-bold text-brand text-right shrink-0">
          Composite: {compositeScore.toFixed(1)} / 100
        </span>
      </div>

      {/* Clean Horizontal Progress Bars (Von Restorff Effect Preserved) */}
      <div className="space-y-3">
        {!scores || factors.length === 0 ? (
          <div className="text-center text-textSecondary text-xs py-4">
            No supplier selected for breakdown.
          </div>
        ) : (
          factors.map((factor) => (
            <div key={factor.name} className="space-y-1">
              <div className="flex items-center justify-between text-xs">
                <span className="text-textPrimary font-semibold">
                  {factor.name} <span className="text-textMuted font-normal">({factor.weight})</span>
                </span>
                <span className="font-extrabold text-textPrimary num-tabular">{factor.score.toFixed(1)}</span>
              </div>
              <div className="w-full bg-surfaceSubtle h-2 rounded-full overflow-hidden">
                <div
                  className={`h-full rounded-full transition-all duration-500 ${
                    factor.score >= 95
                      ? 'bg-success'
                      : factor.score >= 85
                      ? 'bg-textPrimary'
                      : factor.score >= 70
                      ? 'bg-brand'
                      : 'bg-warning'
                  }`}
                  style={{ width: `${Math.max(0, Math.min(100, factor.score))}%` }}
                />
              </div>
              <div className="text-[10px] text-textSecondary leading-tight font-mono">
                → {factor.contribution}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};
