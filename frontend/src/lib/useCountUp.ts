'use client';

import { useState, useEffect } from 'react';

export function useCountUp(target: number, duration: number = 600, decimals: number = 1): number {
  const [count, setCount] = useState<number>(0);

  useEffect(() => {
    let startTimestamp: number | null = null;
    let animationFrameId: number;

    const step = (timestamp: number) => {
      if (!startTimestamp) startTimestamp = timestamp;
      const progress = Math.min((timestamp - startTimestamp) / duration, 1);

      // Ease-out quad formula for smooth decelerating animation
      const easedProgress = 1 - (1 - progress) * (1 - progress);
      const currentVal = Number((easedProgress * target).toFixed(decimals));

      setCount(currentVal);

      if (progress < 1) {
        animationFrameId = requestAnimationFrame(step);
      }
    };

    animationFrameId = requestAnimationFrame(step);

    return () => cancelAnimationFrame(animationFrameId);
  }, [target, duration, decimals]);

  return count;
}
