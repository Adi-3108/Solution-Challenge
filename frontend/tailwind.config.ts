import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: "class",
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        brand: {
          600: "#4F46E5",
          700: "#4338CA",
        },
        success: "#16A34A",
        warning: "#D97706",
        danger: "#DC2626",
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "ui-monospace", "monospace"],
      },
      boxShadow: {
        panel: "0 20px 40px rgba(15, 23, 42, 0.08)",
      },
      backgroundImage: {
        "hero-grid":
          "radial-gradient(circle at top left, rgba(79,70,229,0.16), transparent 36%), radial-gradient(circle at bottom right, rgba(20,184,166,0.16), transparent 34%)",
      },
    },
  },
  plugins: [],
};

export default config;

