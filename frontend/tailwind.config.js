/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        coffee: {
          dark: "#0D0F0A",
          espresso: "#3B1F0E",
          crema: "#C8922A",
          parchment: "#EDE8DC",
        },
        severity: {
          critical: "#EF4444",
          warning: "#F59E0B",
          info: "#3B82F6",
        }
      },
      fontFamily: {
        serif: ["'DM Serif Display'", 'Fraunces', 'serif'],
        mono: ["'JetBrains Mono'", "'IBM Plex Mono'", 'monospace'],
      },
    },
  },
  plugins: [],
}

