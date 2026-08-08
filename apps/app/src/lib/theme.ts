export type Theme = "light" | "dark";

export function currentTheme(): Theme {
  return document.documentElement.getAttribute("data-theme") === "dark" ? "dark" : "light";
}

export function setTheme(theme: Theme) {
  document.documentElement.setAttribute("data-theme", theme);
}

/** Prototype behavior: follow the OS preference on first load. */
export function initTheme() {
  if (window.matchMedia?.("(prefers-color-scheme: dark)").matches) setTheme("dark");
}
