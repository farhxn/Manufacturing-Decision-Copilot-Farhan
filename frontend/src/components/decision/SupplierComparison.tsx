'use client';

import React from 'react';

interface SupplierData {
  supplier_name: string;
  final_score: number;
  lead_time_days: number;
  scores: {
    risk_score: number;
    landed_cost: number;
  };
}

interface Props {
  topSupplier?: SupplierData;
  runnerUp?: SupplierData;
}

export const SupplierComparison: React.FC<Props> = ({ topSupplier, runnerUp }) => {
  if (!topSupplier || !runnerUp) return null;

  const delta = (topSupplier.final_score - runnerUp.final_score).toFixed(1);
  const priceDelta = (runnerUp.scores.landed_cost - topSupplier.scores.landed_cost).toFixed(2);
  const leadTimeDelta = Math.abs(runnerUp.lead_time_days - topSupplier.lead_time_days);

  return (
    <div className="bg-surface p-5 rounded-xl border border-borderDefault shadow-card space-y-4 select-none">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between border-b border-borderDefault pb-3 gap-1">
        <div>
          <span className="text-[10px] font-bold text-textMuted uppercase tracking-wider">Analytical Trade-Offs</span>
          <h4 className="text-sm font-bold text-textPrimary">
            #1 {topSupplier.supplier_name} vs #2 {runnerUp.supplier_name}
          </h4>
        </div>
        <span className="text-xs font-semibold text-brand shrink-0">Delta: +{delta} pts</span>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 sm:gap-4 text-xs">
        {/* Top Supplier Column */}
        <div className="p-3.5 rounded-lg bg-brandSubtle/30 border border-brand/30 space-y-2">
          <div className="flex items-center justify-between font-bold text-textPrimary">
            <span className="truncate mr-2">{topSupplier.supplier_name} (#1)</span>
            <span className="text-brand num-tabular">{topSupplier.final_score.toFixed(1)}</span>
          </div>
          <ul className="space-y-1 text-textSecondary">
            <li className="text-success font-semibold">✓ Higher Composite Score</li>
            <li className="text-success font-semibold">✓ Risk Index ({topSupplier.scores.risk_score.toFixed(1)})</li>
            <li>• {topSupplier.lead_time_days} days Lead Time</li>
            <li className="text-textMuted">• Landed Cost: ${topSupplier.scores.landed_cost.toFixed(2)} / unit</li>
          </ul>
        </div>

        {/* Runner Up Column */}
        <div className="p-3.5 rounded-lg bg-surfaceSubtle border border-borderDefault space-y-2">
          <div className="flex items-center justify-between font-bold text-textPrimary">
            <span className="truncate mr-2">{runnerUp.supplier_name} (#2)</span>
            <span className="text-textMuted num-tabular">{runnerUp.final_score.toFixed(1)}</span>
          </div>
          <ul className="space-y-1 text-textSecondary">
            {runnerUp.scores.landed_cost < topSupplier.scores.landed_cost ? (
              <li className="text-success font-semibold">✓ ${Math.abs(parseFloat(priceDelta))} lower unit price</li>
            ) : (
              <li className="text-warning">• ${parseFloat(priceDelta)} higher unit price</li>
            )}
            
            {runnerUp.lead_time_days > topSupplier.lead_time_days ? (
              <li className="text-warning">• {runnerUp.lead_time_days} days Lead Time (+{leadTimeDelta} days)</li>
            ) : (
              <li className="text-success font-semibold">✓ {runnerUp.lead_time_days} days Lead Time (-{leadTimeDelta} days)</li>
            )}
            <li>• Risk Index: {runnerUp.scores.risk_score.toFixed(1)}</li>
          </ul>
        </div>
      </div>
    </div>
  );
};
