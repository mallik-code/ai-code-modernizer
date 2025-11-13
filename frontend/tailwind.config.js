/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: '#2563EB',
        secondary: '#10B981',
        accent: '#F59E0B',
        error: '#EF4444',
        background: '#0F172A',
        text: '#F8FAFC',
      },
    },
  },
  plugins: [],
}
