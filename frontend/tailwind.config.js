/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        surface: {
          900: '#0a0e1a',
          800: '#0d1220',
          700: '#111827',
          600: '#1a2234',
          500: '#1e2a3d',
        },
        accent: {
          green: '#00d084',
          red: '#ff4d4d',
          blue: '#3b82f6',
          gold: '#f59e0b',
        },
      },
      fontFamily: {
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
      },
    },
  },
  plugins: [],
}
