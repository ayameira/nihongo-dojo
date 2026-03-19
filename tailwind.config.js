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
        ink: {
          DEFAULT: 'var(--ink)',
          light: 'var(--ink-light)',
          muted: 'var(--ink-muted)',
        },
        paper: {
          DEFAULT: 'var(--paper)',
          warm: 'var(--paper-warm)',
          dark: 'var(--paper-dark)',
        },
        vermillion: {
          DEFAULT: 'var(--vermillion)',
          soft: 'var(--vermillion-soft)',
        },
        jade: {
          DEFAULT: 'var(--jade)',
          soft: 'var(--jade-soft)',
        },
      },
    },
  },
  plugins: [],
}

