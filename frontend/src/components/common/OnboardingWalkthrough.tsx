'use client';

import React, { useState, useEffect } from 'react';
import { X, ArrowRight, ArrowLeft, CheckCircle2, Sliders, FileText, Award } from 'lucide-react';

interface Step {
  title: string;
  description: string;
  icon: React.ElementType;
}

const steps: Step[] = [
  {
    title: '1. Decision Score & Arc',
    description: 'The composite score (0-100) weighs Landed Cost, Delivery, Risk, Quality, and Compliance using an auditable formula.',
    icon: Award,
  },
  {
    title: '2. Source Excerpts',
    description: 'Every claim is backed by exact text excerpts extracted directly from verified vendor quotation PDFs.',
    icon: FileText,
  },
  {
    title: '3. Sensitivity Simulator',
    description: 'Drag freight and delay sliders to test what-if scenarios and see when supplier rankings flip.',
    icon: Sliders,
  },
  {
    title: '4. Full Decision Reasoning',
    description: 'Click "Why this supplier?" to inspect eligibility, commercial, delivery, risk, and evidence inputs.',
    icon: CheckCircle2,
  },
];

export const OnboardingWalkthrough: React.FC<{ forceOpen?: boolean; onClose?: () => void }> = ({
  forceOpen = false,
  onClose,
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [currentStep, setCurrentStep] = useState(0);

  useEffect(() => {
    if (forceOpen) {
      setIsOpen(true);
      return;
    }
    const dismissed = localStorage.getItem('mdc_walkthrough_dismissed');
    if (!dismissed) {
      setIsOpen(true);
    }
  }, [forceOpen]);

  const handleDismiss = () => {
    localStorage.setItem('mdc_walkthrough_dismissed', 'true');
    setIsOpen(false);
    if (onClose) onClose();
  };

  if (!isOpen) return null;

  const current = steps[currentStep];
  const Icon = current.icon;

  return (
    <div className="fixed bottom-6 right-6 z-50 select-none animate-entrance">
      {/* Compact Non-Intrusive Integrated Floating Card */}
      <div className="bg-surface w-80 rounded-2xl border border-borderStrong shadow-2xl p-4 space-y-3">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-borderDefault pb-2">
          <div className="flex items-center space-x-1.5">
            <span className="px-2 py-0.5 rounded text-[9px] font-mono font-bold bg-brandSubtle text-brand uppercase tracking-wider">
              TOUR · {currentStep + 1} OF 4
            </span>
          </div>
          <button
            onClick={handleDismiss}
            className="p-1 rounded-lg text-textMuted hover:text-textPrimary hover:bg-surfaceSubtle transition-all"
          >
            <X className="w-3.5 h-3.5" />
          </button>
        </div>

        {/* Step Body */}
        <div className="space-y-1.5">
          <div className="flex items-center space-x-2">
            <div className="p-1.5 rounded-lg bg-brandSubtle text-brand shrink-0">
              <Icon className="w-4 h-4" />
            </div>
            <h4 className="text-xs font-bold text-textPrimary">{current.title}</h4>
          </div>
          <p className="text-[11px] text-textSecondary leading-relaxed pl-1">
            {current.description}
          </p>
        </div>

        {/* Progress Bar */}
        <div className="w-full bg-surfaceSubtle h-1 rounded-full overflow-hidden">
          <div
            className="bg-brand h-full transition-all duration-300 rounded-full"
            style={{ width: `${((currentStep + 1) / steps.length) * 100}%` }}
          />
        </div>

        {/* Footer Actions */}
        <div className="flex items-center justify-between pt-1">
          <button
            onClick={() => setCurrentStep(Math.max(0, currentStep - 1))}
            disabled={currentStep === 0}
            className={`px-2 py-1 text-[11px] font-semibold rounded ${
              currentStep === 0
                ? 'text-textDisabled cursor-not-allowed'
                : 'text-textSecondary hover:text-textPrimary hover:bg-surfaceSubtle'
            }`}
          >
            <ArrowLeft className="w-3 h-3 inline mr-1" /> Prev
          </button>

          {currentStep < steps.length - 1 ? (
            <button
              onClick={() => setCurrentStep(currentStep + 1)}
              className="px-3 py-1 text-[11px] font-semibold bg-surfaceInk text-surface rounded-lg hover:opacity-90 transition-all flex items-center"
            >
              Next <ArrowRight className="w-3 h-3 ml-1 text-brand" />
            </button>
          ) : (
            <button
              onClick={handleDismiss}
              className="px-3 py-1 text-[11px] font-semibold bg-brand text-white rounded-lg hover:bg-brand-hover transition-all flex items-center"
            >
              Start <CheckCircle2 className="w-3 h-3 ml-1" />
            </button>
          )}
        </div>
      </div>
    </div>
  );
};
