import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: ["class"],
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        background: "rgb(var(--bg))",
        panel: "rgb(var(--panel))",
        "panel-2": "rgb(var(--panel-2))",
        primary: "rgb(var(--primary))",
        accent: "rgb(var(--accent))",
        muted: "rgb(var(--muted))",
      },
      backgroundImage: {
        "grid-fine": "linear-gradient(rgba(180,165,245,0.04) 1px, transparent 1px), linear-gradient(90deg, rgba(180,165,245,0.04) 1px, transparent 1px)"
      },
      boxShadow: {
        glow: "0 0 0 1px rgba(255,255,255,.05), 0 20px 80px rgba(0,0,0,.5)",
        "glow-violet": "0 0 0 1px rgba(138,99,242,0.1), 0 0 20px rgba(138,99,242,0.15)",
        "glow-violet-lg": "0 0 0 1px rgba(138,99,242,0.2), 0 0 40px rgba(138,99,242,0.25)",
      },
      backdropBlur: {
        xs: "2px"
      }
    }
  },
  plugins: []
};

export default config;
