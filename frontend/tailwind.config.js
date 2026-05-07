/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        bg: "#0F1117",
        surface: "#181B23",
        surface2: "#121520",
        border: "#2A2E3B",
        text: "#E8E9ED",
        muted: "#8B8FA3",
        dim: "#5C6078",
        accent: "#3B82F6",
        green: "#22C55E",
        amber: "#F59E0B",
        red: "#EF4444",
        licensing: "#818CF8",
        endpoint: "#34D399",
        recon: "#FB923C",
      },
      fontFamily: {
        sans: ["DM Sans", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "monospace"],
      },
    },
  },
  plugins: [],
};
