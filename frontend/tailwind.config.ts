import type { Config } from 'tailwindcss';
import plugin from 'tailwindcss/plugin';

/**
 * Cyberpunk-accessible design tokens. Components never hard-code hex values —
 * colors resolve to CSS variables set in `src/styles/index.css` (light default,
 * `[data-theme="dark"]` flips them). Typography is 100% monospace; corners are
 * cut with `clip-path` utilities, not border-radius.
 */
const MONO = [
  '"JetBrains Mono"',
  '"Fira Code"',
  '"Share Tech Mono"',
  'ui-monospace',
  'SFMono-Regular',
  'Menlo',
  'Consolas',
  'monospace',
];

export default {
  darkMode: ['class', '[data-theme="dark"]'],
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      fontFamily: {
        // Monospace everywhere — `sans` is aliased so existing `font-sans`
        // usage and Tailwind's base styles pick up the mono stack too.
        sans: MONO,
        mono: MONO,
      },
      colors: {
        // Semantic tokens — map to CSS variables (HSL channels).
        surface: 'hsl(var(--surface) / <alpha-value>)',
        'surface-muted': 'hsl(var(--surface-muted) / <alpha-value>)',
        'surface-raised': 'hsl(var(--surface-raised) / <alpha-value>)',
        border: 'hsl(var(--border) / <alpha-value>)',
        'border-strong': 'hsl(var(--border-strong) / <alpha-value>)',
        foreground: 'hsl(var(--foreground) / <alpha-value>)',
        'foreground-muted': 'hsl(var(--foreground-muted) / <alpha-value>)',
        primary: 'hsl(var(--primary) / <alpha-value>)',
        'primary-foreground': 'hsl(var(--primary-foreground) / <alpha-value>)',
        success: 'hsl(var(--success) / <alpha-value>)',
        warning: 'hsl(var(--warning) / <alpha-value>)',
        danger: 'hsl(var(--danger) / <alpha-value>)',
        // Neon accents — Cyan / Magenta-Rose / Green (dark), saturated cobalt /
        // fuchsia / emerald (light) for WCAG-AA contrast.
        neon: {
          cyan: 'hsl(var(--accent-1) / <alpha-value>)',
          blue: 'hsl(var(--accent-1) / <alpha-value>)',
          violet: 'hsl(var(--accent-2) / <alpha-value>)',
          magenta: 'hsl(var(--accent-2) / <alpha-value>)', // alias — accent-2 is now violet
          green: 'hsl(var(--accent-3) / <alpha-value>)',
        },
      },
      borderRadius: {
        // Kept so `rounded-card` stays a valid class, but squared off — real
        // shape comes from the `.clip-*` utilities below.
        card: '0px',
      },
      boxShadow: {
        // Clean elevation — one soft ambient shadow, no glow. Default for cards.
        elev: '0 1px 2px hsl(var(--shadow) / 0.06), 0 6px 20px -6px hsl(var(--shadow) / 0.18)',
        'elev-lg': '0 2px 6px hsl(var(--shadow) / 0.08), 0 16px 40px -12px hsl(var(--shadow) / 0.28)',
        // Neon — reserved for hover / active / focus on interactive elements.
        'neon-cyan': '0 0 0 1px hsl(var(--accent-1) / 0.5), 0 0 14px -2px hsl(var(--accent-1) / 0.45)',
        'neon-blue': '0 0 0 1px hsl(var(--accent-1) / 0.5), 0 0 14px -2px hsl(var(--accent-1) / 0.45)',
        'neon-violet':
          '0 0 0 1px hsl(var(--accent-2) / 0.5), 0 0 14px -2px hsl(var(--accent-2) / 0.45)',
        'neon-magenta':
          '0 0 0 1px hsl(var(--accent-2) / 0.5), 0 0 14px -2px hsl(var(--accent-2) / 0.45)',
        'neon-green':
          '0 0 0 1px hsl(var(--accent-3) / 0.5), 0 0 14px -2px hsl(var(--accent-3) / 0.45)',
      },
      keyframes: {
        flicker: {
          '0%, 100%': { opacity: '1' },
          '48%': { opacity: '1' },
          '50%': { opacity: '0.72' },
          '52%': { opacity: '1' },
          '92%': { opacity: '0.85' },
        },
        scan: {
          '0%': { transform: 'translateY(-120%)' },
          '100%': { transform: 'translateY(320%)' },
        },
        'pulse-neon': {
          '0%, 100%': { boxShadow: '0 0 0 1px hsl(var(--accent-1) / 0.5)' },
          '50%': {
            boxShadow: '0 0 0 1px hsl(var(--accent-1) / 0.7), 0 0 18px -2px hsl(var(--accent-1) / 0.5)',
          },
        },
        'fade-in': {
          from: { opacity: '0', transform: 'translateY(8px)' },
          to: { opacity: '1', transform: 'translateY(0)' },
        },
        'flyout-left': {
          from: { opacity: '0', transform: 'translateX(-10px) scale(0.98)' },
          to: { opacity: '1', transform: 'translateX(0) scale(1)' },
        },
        'chat-in': {
          from: { opacity: '0', transform: 'translateY(16px) scale(0.96)' },
          to: { opacity: '1', transform: 'translateY(0) scale(1)' },
        },
        sheen: {
          '0%': { transform: 'translateX(-120%)' },
          '60%, 100%': { transform: 'translateX(320%)' },
        },
      },
      animation: {
        flicker: 'flicker 5s linear infinite',
        scan: 'scan 6s linear infinite',
        'pulse-neon': 'pulse-neon 2.6s ease-in-out infinite',
        'fade-in': 'fade-in 0.4s cubic-bezier(0.16, 1, 0.3, 1) both',
        'flyout-left': 'flyout-left 0.22s cubic-bezier(0.16, 1, 0.3, 1) both',
        'chat-in': 'chat-in 0.28s cubic-bezier(0.16, 1, 0.3, 1) both',
        sheen: 'sheen 2.8s ease-in-out infinite',
      },
    },
  },
  plugins: [
    // Beveled / cut-corner shapes — the cyberpunk replacement for rounded-*.
    plugin(({ addUtilities }) => {
      addUtilities({
        '.clip-bevel': {
          clipPath:
            'polygon(14px 0, 100% 0, 100% calc(100% - 14px), calc(100% - 14px) 100%, 0 100%, 0 14px)',
        },
        '.clip-bevel-sm': {
          clipPath:
            'polygon(7px 0, 100% 0, 100% calc(100% - 7px), calc(100% - 7px) 100%, 0 100%, 0 7px)',
        },
        '.clip-notch': {
          clipPath:
            'polygon(0 0, calc(100% - 16px) 0, 100% 16px, 100% 100%, 16px 100%, 0 calc(100% - 16px))',
        },
        '.clip-tag': {
          clipPath: 'polygon(0 0, 100% 0, 100% 100%, 9px 100%, 0 calc(100% - 9px))',
        },
        '.clip-arrow': {
          clipPath: 'polygon(0 0, calc(100% - 12px) 0, 100% 50%, calc(100% - 12px) 100%, 0 100%)',
        },
      });
    }),
  ],
} satisfies Config;
