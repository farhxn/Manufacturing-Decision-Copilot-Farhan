'use client';

import React from 'react';

interface ScoreArcProps {
  score: number;
  maxScore?: number;
  size?: number;
  strokeWidth?: number;
  label?: string;
  color?: string;
  subColor?: string;
}

export const DonutGauge: React.FC<ScoreArcProps> = ({
  score,
  maxScore = 100,
  size = 90,
  strokeWidth = 4,
  label = 'DECISION SCORE',
  color = 'var(--brand)',
  subColor = 'var(--border)',
}) => {
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const percentage = Math.min(Math.max(score / maxScore, 0), 1);
  const strokeDashoffset = circumference - percentage * circumference;

  return (
    <div className="flex flex-col items-center justify-center select-none">
      <div className="relative flex items-center justify-center" style={{ width: size, height: size }}>
        <svg width={size} height={size} className="transform -rotate-90">
          {/* Subtle Background Arc */}
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            stroke={subColor}
            strokeWidth={strokeWidth}
            fill="transparent"
            strokeDasharray={circumference}
            strokeDashoffset={0}
          />
          {/* Refined Thin Copper Score Arc */}
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            stroke={color}
            strokeWidth={strokeWidth}
            strokeDasharray={circumference}
            strokeDashoffset={strokeDashoffset}
            strokeLinecap="round"
            fill="transparent"
            className="transition-all duration-700 ease-out"
          />
        </svg>
        {/* Center Tabular Score */}
        <div className="absolute inset-0 flex flex-col items-center justify-center text-center">
          <span className="text-2xl font-extrabold text-textPrimary num-tabular leading-none tracking-tight">
            {score.toFixed(1)}
          </span>
          <span className="text-[9px] font-bold text-textMuted tracking-wider uppercase mt-1">
            / 100
          </span>
        </div>
      </div>
      {label && (
        <span className="text-[10px] font-bold text-textMuted tracking-wider uppercase mt-2">
          {label}
        </span>
      )}
    </div>
  );
};
