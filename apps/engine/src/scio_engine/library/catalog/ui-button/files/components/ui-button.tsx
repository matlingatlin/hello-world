import type { ButtonHTMLAttributes, ReactNode } from "react";

type Variant = "primary" | "quiet";

/**
 * The one button. Every surface uses it, so a change to how a button looks is
 * one change — which is the whole point of a token-bound library part.
 */
export function UiButton({
  children,
  variant = "primary",
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement> & { children: ReactNode; variant?: Variant }) {
  const base = "rounded-[__TOKEN_RADIUS__] px-4 py-2 font-medium disabled:opacity-60";
  const look =
    variant === "primary"
      ? "text-white"
      : "border bg-transparent";
  return (
    <button
      {...props}
      style={variant === "primary" ? { background: "__TOKEN_ACCENT__" } : undefined}
      className={`${base} ${look}`}
    >
      {children}
    </button>
  );
}
