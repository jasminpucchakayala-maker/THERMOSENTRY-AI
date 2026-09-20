// C:/Users/jasmi/OneDrive/Desktop/THERMOSENTRY-AI/frontend/tailwind.config.ts
import type { Config } from 'tailwindcss';

export default <Config>{
  content: ['./src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        // Base / surfaces
        'bg-base': '#0D1512',
        'surface-1': '#16211C',
        'surface-2': '#1E2B24',
        'border-muted': '#2A3B32',
        // Text
        'text-muted': '#8FA396',
        'text-primary': '#F3F0E9',
        // Accents
        'accent-primary': '#E88A3C',
        'accent-secondary': '#D4A24E',
        'accent-live': '#FF7A45',
        // Risk gradient
        'risk-low': '#2F9E7A',
        'risk-mod': '#D9A441',
        'risk-high': '#E8622C',
        'risk-crit': '#B32C2C',
        // Classification accents
        'class-industrial': '#C1502E',
        'class-gasflare': '#E4B93F',
        'class-vegetation': '#8C7B3E',
        'class-agri': '#A9714A',
        'class-persistent': '#8B5C8A',
        'class-uncertain': '#6E7A76',
      },
      fontFamily: {
        heading: ['"Space Grotesk"', 'sans-serif'],
        body: ['Inter', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'monospace'],
      },
      animation: {
        pulseGlow: 'pulseGlow 2s infinite',
      },
      keyframes: {
        pulseGlow: {
          '0%,100%': { boxShadow: '0 0 8px #FF7A45' },
          '50%': { boxShadow: '0 0 16px #FF7A45' },
        },
      },
    },
  },
  plugins: [],
};
