/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        bgApp: 'var(--bg-app)',
        surface: 'var(--surface)',
        surfaceSubtle: 'var(--surface-subtle)',
        surfaceTertiary: 'var(--surface-tertiary)',
        surfaceInk: 'var(--surface-ink)',

        textPrimary: 'var(--text-primary)',
        textSecondary: 'var(--text-secondary)',
        textMuted: 'var(--text-muted)',
        textDisabled: 'var(--text-disabled)',

        borderDefault: 'var(--border)',
        borderStrong: 'var(--border-strong)',
        divider: 'var(--divider)',

        brand: {
          DEFAULT: 'var(--brand)',
          hover: 'var(--brand-hover)',
          active: 'var(--brand-active)',
          subtle: 'var(--brand-subtle)',
        },
        success: {
          DEFAULT: 'var(--success)',
          subtle: 'var(--success-subtle)',
        },
        warning: {
          DEFAULT: 'var(--warning)',
          subtle: 'var(--warning-subtle)',
        },
        danger: {
          DEFAULT: 'var(--danger)',
          subtle: 'var(--danger-subtle)',
        },
        info: {
          DEFAULT: 'var(--info)',
          subtle: 'var(--info-subtle)',
        },
      },
      borderRadius: {
        card: '12px',
      },
      boxShadow: {
        card: 'var(--shadow-card)',
        elevation: '0 4px 12px rgba(25, 25, 24, 0.06)',
      },
    },
  },
  plugins: [],
};
