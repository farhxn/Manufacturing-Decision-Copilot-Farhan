'use client';

import React, { useState } from 'react';
import { ArrowUp, ArrowDown, Sliders, Info, RotateCcw, AlertTriangle } from 'lucide-react';

export const ScenarioSimulator: React.FC<{
  topSupplier?: { supplier_name: string; final_score: number; country: string } | null;
  runnerUp?: { supplier_name: string; final_score: number; country: string } | null;
}> = ({ topSupplier, runnerUp }) => {
  const [shippingCost, setShippingCost] = useState(0); // +0% to +50%
  const [leadTime, setLeadTime] = useState(0); // 0 to +15 days

  // Dynamic flip threshold based on score difference (if available)
  // Just a simple visual mock heuristic for the dashboard:
  const diff = topSupplier && runnerUp ? topSupplier.final_score - runnerUp.final_score : 5;
  const shippingThreshold = Math.max(10, diff * 5); // Example heuristic
  const leadTimeThreshold = Math.max(5, diff * 2);

  const isFlipped = shippingCost >= shippingThreshold || leadTime >= leadTimeThreshold;

  const handleReset = () => {
    setShippingCost(0);
    setLeadTime(0);
  };

  if (!topSupplier || !runnerUp) {
    return (
      <div id="scenario-simulator" className="bg-surface p-4 sm:p-5 rounded-xl border border-borderDefault shadow-card space-y-4 select-none">
        <div className="flex items-center space-x-2 border-b border-borderDefault pb-3">
          <Sliders className="w-4 h-4 text-brand shrink-0" />
          <div>
            <span className="text-[10px] font-bold text-textMuted uppercase tracking-wider">Direct Manipulation</span>
            <h4 className="text-sm font-bold text-textPrimary">Scenario What-If Simulator</h4>
          </div>
        </div>
        <div className="text-center py-6 text-xs text-textSecondary">
          Requires at least two evaluated suppliers to simulate ranking changes.
        </div>
      </div>
    );
  }

  const topName = topSupplier.supplier_name;
  const runnerName = runnerUp.supplier_name;

  return (
    <div id="scenario-simulator" className="bg-surface p-4 sm:p-5 rounded-xl border border-borderDefault shadow-card space-y-4 select-none">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between border-b border-borderDefault pb-3 gap-2">
        <div className="flex items-center space-x-2">
          <Sliders className="w-4 h-4 text-brand shrink-0" />
          <div>
            <span className="text-[10px] font-bold text-textMuted uppercase tracking-wider">Direct Manipulation</span>
            <h4 className="text-sm font-bold text-textPrimary">Scenario What-If Simulator</h4>
          </div>
        </div>
        {(shippingCost > 0 || leadTime > 0) && (
          <button
            onClick={handleReset}
            className="text-xs font-semibold text-brand hover:text-brand-hover flex items-center transition-all self-start sm:self-auto"
          >
            <RotateCcw className="w-3 h-3 mr-1" /> Reset Baseline
          </button>
        )}
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 sm:gap-6">
        {/* Sliders */}
        <div className="space-y-4">
          <div className="space-y-1.5">
            <div className="flex justify-between text-xs">
              <span className="font-semibold text-textPrimary">Freight & Shipping Cost Increase</span>
              <span className="font-bold text-brand num-tabular">+{shippingCost}%</span>
            </div>
            <input
              type="range"
              min="0"
              max="100"
              step="5"
              value={shippingCost}
              onChange={(e) => setShippingCost(Number(e.target.value))}
              className="w-full h-1.5 bg-surfaceSubtle rounded-lg appearance-none cursor-pointer accent-brand"
            />
          </div>

          <div className="space-y-1.5">
            <div className="flex justify-between text-xs">
              <span className="font-semibold text-textPrimary">Transit / Port Delay</span>
              <span className="font-bold text-brand num-tabular">+{leadTime} Days</span>
            </div>
            <input
              type="range"
              min="0"
              max="30"
              step="1"
              value={leadTime}
              onChange={(e) => setLeadTime(Number(e.target.value))}
              className="w-full h-1.5 bg-surfaceSubtle rounded-lg appearance-none cursor-pointer accent-brand"
            />
          </div>
        </div>

        {/* Dynamic Rank Outcome Box */}
        <div className={`p-4 rounded-lg border transition-all duration-300 ${
          isFlipped
            ? 'bg-warningSubtle border-warning shadow-sm'
            : 'bg-surfaceSubtle border-borderDefault'
        }`}>
          <div className="text-xs font-bold text-textPrimary flex items-center justify-between mb-2">
            <span className="flex items-center">
              {isFlipped && <AlertTriangle className="w-3.5 h-3.5 text-warning mr-1.5" />}
              {isFlipped ? 'DECISION FLIPPED' : 'BASELINE STABLE'}
            </span>
            <span className="text-[10px] font-mono text-textMuted">
              {isFlipped ? 'THRESHOLD EXCEEDED' : 'CURRENT OPTIMAL'}
            </span>
          </div>

          {/* Animated Movement Rows */}
          <div className="space-y-2 text-xs">
            <div className={`flex items-center justify-between p-2.5 rounded transition-all duration-300 border ${
              isFlipped ? 'bg-surface border-warning/40 font-bold' : 'bg-surface border-borderDefault font-semibold'
            }`}>
              <span className="text-textPrimary truncate mr-2">
                {isFlipped ? runnerName : topName}
              </span>
              <div className="flex items-center text-success font-bold shrink-0">
                <span className="mr-1.5">Rank #1</span>
                {isFlipped && <ArrowUp className="w-3.5 h-3.5 text-success animate-bounce" />}
              </div>
            </div>

            <div className={`flex items-center justify-between p-2.5 rounded transition-all duration-300 border ${
              isFlipped ? 'bg-surface border-danger/40' : 'bg-surface border-borderDefault'
            }`}>
              <span className="text-textSecondary truncate mr-2">
                {isFlipped ? topName : runnerName}
              </span>
              <div className="flex items-center text-warning font-bold shrink-0">
                <span className="mr-1.5">Rank #2</span>
                {isFlipped && <ArrowDown className="w-3.5 h-3.5 text-danger" />}
              </div>
            </div>
          </div>

          {/* Plain Explanation Banner */}
          <div className="text-[11px] text-textSecondary leading-relaxed pt-2.5 mt-2.5 border-t border-divider flex items-start space-x-1.5">
            <Info className="w-3.5 h-3.5 text-brand shrink-0 mt-0.5" />
            <div>
              {isFlipped ? (
                <span>
                  <strong>Threshold Reached:</strong> Shipping cost increased {shippingCost}%. {topName}'s landed-cost advantage disappeared. {runnerName} ({runnerUp.country}) becomes the #1 recommendation instead.
                </span>
              ) : (
                <span>
                  {topName} remains the #1 recommendation unless shipping costs rise above {Math.ceil(shippingThreshold)}% or transit delays exceed +{Math.ceil(leadTimeThreshold)} days.
                </span>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
