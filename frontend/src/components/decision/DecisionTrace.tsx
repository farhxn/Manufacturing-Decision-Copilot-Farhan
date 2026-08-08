'use client';

import React from 'react';
import { ArrowRight, CheckCircle2, AlertTriangle, ShieldCheck, Cpu, Trophy, FileText } from 'lucide-react';

interface Stage {
  label: string;
  count: string;
  description: string;
  status: 'passed' | 'warning' | 'final';
  icon: React.ElementType;
}

const stages: Stage[] = [
  {
    label: 'REQUIREMENTS',
    count: '2 Mandatory',
    description: 'ISO 9001 + AS9100D',
    status: 'passed',
    icon: ShieldCheck,
  },
  {
    label: 'ELIGIBILITY',
    count: '3 Qualified',
    description: '2 Disqualified',
    status: 'warning',
    icon: Cpu,
  },
  {
    label: 'EVIDENCE',
    count: '10 Excerpts',
    description: '3 Source Documents',
    status: 'passed',
    icon: FileText,
  },
  {
    label: 'VERIFICATION',
    count: '2 Verified',
    description: '0 Conflicts',
    status: 'passed',
    icon: CheckCircle2,
  },
  {
    label: 'SCORING',
    count: '88.5 Score',
    description: 'Deterministic Engine',
    status: 'passed',
    icon: ShieldCheck,
  },
  {
    label: 'RECOMMENDATION',
    count: 'Acme Precision',
    description: 'Rank #1 Optimal Choice',
    status: 'final',
    icon: Trophy,
  },
];

export const DecisionTrace: React.FC = () => {
  return (
    <div id="decision-trace" className="bg-[#191918] text-[#FFFDF9] p-6 rounded-xl border border-[#302F2C] shadow-lg space-y-4 relative overflow-hidden select-none">
      {/* Localized technical blueprint grid overlay */}
      <div className="absolute inset-0 bg-tech-grid opacity-5 pointer-events-none" />

      {/* Header */}
      <div className="flex items-center justify-between relative z-10">
        <div>
          <span className="text-[10px] font-mono font-bold text-[#807F79] uppercase tracking-widest">
            Immersive Dark Section · Decision Pipeline
          </span>
          <h4 className="text-sm font-bold text-[#FFFDF9] tracking-tight mt-0.5">
            Causal Decision Chain & Auditability
          </h4>
        </div>
        <span className="text-xs font-mono font-medium text-[#4F7868] bg-[#E7F0EB]/10 border border-[#4F7868]/40 px-3 py-1 rounded-md">
          ● Deterministic Verification
        </span>
      </div>

      {/* 6-Stage Connected Pipeline Nodes */}
      <div className="relative z-10 pt-1 -mx-1">
        {/* Mobile: horizontal scroll; md+: 6-col grid */}
        <div className="flex md:grid md:grid-cols-6 gap-2.5 overflow-x-auto pb-2 md:pb-0 md:overflow-visible">
        {stages.map((stage, idx) => {
          const Icon = stage.icon;
          return (
            <div
              key={stage.label}
              className={`relative p-3.5 rounded-xl border transition-all shrink-0 w-[140px] md:w-auto ${
                stage.status === 'final'
                  ? 'bg-[#252423] border-[#C56A32] shadow-md shadow-[#C56A32]/10'
                  : stage.status === 'warning'
                  ? 'bg-[#201F1E] border-[#B98532]/50'
                  : 'bg-[#201F1E] border-[#302F2C]'
              }`}
            >
              <div className="flex items-center justify-between mb-1.5">
                <div
                  className={`p-1.5 rounded-lg ${
                    stage.status === 'final'
                      ? 'bg-[#C56A32]/20 text-[#C56A32]'
                      : stage.status === 'warning'
                      ? 'bg-[#B98532]/20 text-[#B98532]'
                      : 'bg-[#4F7868]/20 text-[#4F7868]'
                  }`}
                >
                  <Icon className="w-3.5 h-3.5" />
                </div>
                <span className="text-[9px] font-mono text-[#807F79]">0{idx + 1}</span>
              </div>

              <div className="text-[11px] font-bold text-[#FFFDF9] tracking-wider uppercase">{stage.label}</div>
              <div className={`text-xs font-semibold num-tabular mt-0.5 ${stage.status === 'final' ? 'text-[#C56A32]' : 'text-[#FFFDF9]'}`}>
                {stage.count}
              </div>
              <div className="text-[9px] text-[#807F79] mt-0.5">{stage.description}</div>

              {/* Connecting Pipeline Line — desktop only */}
              {idx < stages.length - 1 && (
                <div className="hidden md:flex absolute -right-2.5 top-1/2 -translate-y-1/2 z-20 w-5 h-5 items-center justify-center bg-[#252423] border border-[#302F2C] rounded-full text-[#807F79]">
                  <ArrowRight className="w-2.5 h-2.5" />
                </div>
              )}
            </div>
          );
        })}
        </div>
      </div>
    </div>
  );
};
