/** @type {import('tailwindcss').Config} */
module.exports = {
   content: [
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'ubs-red': '#e60000',
        'ubs-black': '#000000',
        'ubs-white': '#ffffff',
      }
    },
  },
  plugins: [],
}

