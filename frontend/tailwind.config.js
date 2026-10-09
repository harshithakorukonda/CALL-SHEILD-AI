/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      boxShadow: {
        glow: '0 0 0 1px rgba(96, 165, 250, 0.35), 0 10px 30px rgba(14, 116, 144, 0.25)',
      },
    },
  },
  plugins: [],
}
