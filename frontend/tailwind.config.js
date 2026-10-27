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
        dev: {
          bg: '#0d1117',
          surface: '#161b22',
          card: '#1c2128',
          border: '#30363d',
          accent: '#58a6ff',
          muted: '#8b949e',
          text: '#c9d1d9',
          heading: '#f0f6fc',
          success: '#3fb950',
          warning: '#d29922',
          danger: '#f85149',
          purple: '#bc8cff',
          cyan: '#39c5cf',
        }
      },
      fontFamily: {
        mono: ['"JetBrains Mono"', 'Consolas', 'Monaco', '"Fira Code"', 'monospace'],
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
      }
    },
  },
  plugins: [],
}
