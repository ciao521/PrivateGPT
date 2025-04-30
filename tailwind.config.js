/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: 'class',
  content: ['./templates/*.{html,js}', 'node_modules/preline/dist/*.js'],
  theme: {
    extend: {},
  },
  plugins: [
    require('preline/plugin'),
  ],
}

