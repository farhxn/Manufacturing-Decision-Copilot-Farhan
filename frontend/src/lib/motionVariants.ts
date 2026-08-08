/**
 * motionVariants.ts
 *
 * Shared Framer Motion variants used across pages.
 * All durations stay under 700ms per design system rules (§14.3).
 * Respects prefers-reduced-motion via Framer Motion's built-in support.
 */

import type { Variants } from 'framer-motion';

/** Fade + slide-up entrance for a single item */
export const itemVariants: Variants = {
  hidden: { opacity: 0, y: 10 },
  show:   { opacity: 1, y: 0, transition: { duration: 0.28, ease: [0.16, 1, 0.3, 1] } },
};

/** Parent that staggers its children */
export const listVariants: Variants = {
  hidden: {},
  show:   { transition: { staggerChildren: 0.055, delayChildren: 0.05 } },
};

/** Faster stagger for dense lists (table rows, chunk cards) */
export const denseListVariants: Variants = {
  hidden: {},
  show:   { transition: { staggerChildren: 0.035, delayChildren: 0.02 } },
};

/** Single fade-up with configurable delay — use on hero/section cards */
export const sectionVariants: Variants = {
  hidden: { opacity: 0, y: 14 },
  show:   { opacity: 1, y: 0, transition: { duration: 0.38, ease: [0.16, 1, 0.3, 1] } },
};

/** Horizontal slide-in from left — used for drawers / side panels */
export const slideInVariants: Variants = {
  hidden: { opacity: 0, x: -12 },
  show:   { opacity: 1, x: 0,  transition: { duration: 0.3,  ease: [0.16, 1, 0.3, 1] } },
};

/** Scale-up pop — used for badges, score numbers */
export const popVariants: Variants = {
  hidden: { opacity: 0, scale: 0.88 },
  show:   { opacity: 1, scale: 1,    transition: { duration: 0.22, ease: [0.34, 1.56, 0.64, 1] } },
};
