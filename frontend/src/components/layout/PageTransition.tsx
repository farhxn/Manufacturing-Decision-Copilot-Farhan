'use client';

/**
 * PageTransition — Framer Motion wrapper for page-level route changes.
 *
 * Wraps each page's content in a motion.div that fades + slides up on mount
 * and fades out on unmount. The key is set by the caller (typically the
 * current pathname) so Framer Motion knows when to re-run the animation.
 *
 * Design constraints (per roadmap §14.3):
 * - Duration < 700ms
 * - Purpose-driven — only on actual navigation, never decorative
 * - Respects prefers-reduced-motion via Framer Motion's built-in support
 */

import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';

interface PageTransitionProps {
  children: React.ReactNode;
  /** Unique key — change this to trigger the animation (use pathname) */
  routeKey: string;
}

const variants = {
  initial: { opacity: 0, y: 10 },
  enter:   { opacity: 1, y: 0,  transition: { duration: 0.32, ease: [0.16, 1, 0.3, 1] } },
  exit:    { opacity: 0, y: -6, transition: { duration: 0.18, ease: 'easeIn' } },
};

export function PageTransition({ children, routeKey }: PageTransitionProps) {
  return (
    <AnimatePresence mode="wait" initial={false}>
      <motion.div
        key={routeKey}
        variants={variants}
        initial="initial"
        animate="enter"
        exit="exit"
        // Stretch to fill the parent main area
        style={{ minHeight: '100%' }}
      >
        {children}
      </motion.div>
    </AnimatePresence>
  );
}
