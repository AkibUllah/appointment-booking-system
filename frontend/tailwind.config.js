/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        brand: { 50: '#eef7f4', 100: '#d5ece3', 500: '#0f8a6a', 600: '#0b6f55', 700: '#085643' },
      },
      fontFamily: { sans: ['Inter', 'Noto Sans Bengali', 'system-ui', 'sans-serif'] },
    },
  },
  plugins: [],
};
