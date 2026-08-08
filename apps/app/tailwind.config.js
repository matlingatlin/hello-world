/** Tokens from docs/DESIGN.md — single source of truth. Values live as CSS
 * variables in src/styles.css so the dark theme swaps without a rebuild. */
/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "var(--ink)",
        muted: "var(--muted)",
        paper: "var(--paper)",
        surface: "var(--surface)",
        "surface-2": "var(--surface-2)",
        line: "var(--line)",
        "line-strong": "var(--line-strong)",
        teal: "var(--teal)",
        "teal-hover": "var(--teal-hover)",
        "teal-tint": "var(--teal-tint)",
        verified: "var(--verified)",
        attention: "var(--attention)",
        danger: "var(--error)",
        "on-teal": "var(--on-teal)",
      },
      borderRadius: {
        card: "7px",
        btn: "5px",
      },
      fontFamily: {
        display: ['"Space Grotesk"', "sans-serif"],
        sans: ['"IBM Plex Sans"', "system-ui", "sans-serif"],
        mono: ['"IBM Plex Mono"', "monospace"],
      },
    },
  },
  plugins: [],
};
