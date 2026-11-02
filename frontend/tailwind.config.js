/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        // Semantic colors - ONLY for state communication
        success: '#059669',
        warning: '#d97706',
        critical: '#dc2626',
        info: '#2563eb',

        // Neutral backgrounds
        base: '#ffffff',
        surface: '#f8fafc',
        elevated: '#ffffff',
        hover: '#f1f5f9',
        active: '#e2e8f0',

        // Borders
        border: '#e2e8f0',
        'border-emphasis': '#94a3b8',

        // Text
        text: '#0f172a',
        'text-secondary': '#475569',
        'text-muted': '#94a3b8',
        'text-inverse': '#ffffff',

        // Charts - categorical (colorblind safe)
        chart: {
          1: '#0ea5e9',
          2: '#22c55e',
          3: '#f59e0b',
          4: '#ef4444',
          5: '#8b5cf6',
          6: '#ec4899',
          7: '#06b6d4',
          8: '#84cc16',
        },

        // Gauge bands
        gauge: {
          good: '#059669',
          warn: '#d97706',
          crit: '#dc2626',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      fontSize: {
        display: ['3rem', { lineHeight: '1.1', fontWeight: '600' }],
        h1: ['2rem', { lineHeight: '1.2', fontWeight: '600' }],
        h2: ['1.5rem', { lineHeight: '1.3', fontWeight: '600' }],
        h3: ['1.25rem', { lineHeight: '1.3', fontWeight: '600' }],
        'body-lg': ['1.125rem', { lineHeight: '1.5' }],
        body: ['1rem', { lineHeight: '1.5' }],
        'body-sm': ['0.875rem', { lineHeight: '1.5' }],
        caption: ['0.75rem', { lineHeight: '1.4', fontWeight: '500' }],
        data: ['1rem', { lineHeight: '1.2', fontWeight: '500' }],
        'data-lg': ['2rem', { lineHeight: '1.1', fontWeight: '600' }],
        'data-xl': ['3rem', { lineHeight: '1', fontWeight: '700' }],
      },
      spacing: {
        1: '4px',
        2: '8px',
        3: '12px',
        4: '16px',
        5: '20px',
        6: '24px',
        8: '32px',
        10: '40px',
        12: '48px',
        16: '64px',
        18: '72px',
        20: '80px',
        24: '96px',
      },
      borderRadius: {
        card: '12px',
        button: '8px',
        input: '8px',
      },
      animation: {
        'fade-in': 'fadeIn 200ms ease-out',
        'slide-up': 'slideUp 200ms ease-out',
        'slide-down': 'slideDown 300ms ease-out',
        'pulse-critical': 'pulseCritical 1000ms ease-in-out infinite',
        'gauge-sweep': 'gaugeSweep 600ms ease-out',
        'value-transition': 'valueTransition 300ms ease-out',
        'shimmer': 'shimmer 1500ms linear infinite',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { opacity: '0', transform: 'translateY(8px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        slideDown: {
          '0%': { opacity: '0', transform: 'translateY(-8px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        pulseCritical: {
          '0%, 100%': { transform: 'scale(1)' },
          '50%': { transform: 'scale(1.02)' },
        },
        gaugeSweep: {
          '0%': { strokeDashoffset: '100%' },
          '100%': { strokeDashoffset: '0%' },
        },
        valueTransition: {
          '0%': { opacity: '0.5' },
          '100%': { opacity: '1' },
        },
        shimmer: {
          '0%': { backgroundPosition: '-200% 0' },
          '100%': { backgroundPosition: '200% 0' },
        },
      },
      boxShadow: {
        card: '0 1px 3px 0 rgb(0 0 0 / 0.1), 0 1px 2px -1px rgb(0 0 0 / 0.1)',
        'card-hover': '0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1)',
        elevated: '0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1)',
      },
    },
  },
  plugins: [],
}