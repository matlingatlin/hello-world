import type { ButtonHTMLAttributes, ReactNode } from "react";
import type { ProjectStatus } from "@scio/shared";

export function Eyebrow({ children }: { children: ReactNode }) {
  return (
    <span className="font-mono text-[11px] uppercase tracking-[0.14em] text-muted">{children}</span>
  );
}

export function PageTitle({ children }: { children: ReactNode }) {
  return (
    <h1 className="font-display text-[28px] font-semibold tracking-tight mt-2 mb-1">{children}</h1>
  );
}

export function Lede({ children }: { children: ReactNode }) {
  return <p className="text-[15px] text-muted mb-6">{children}</p>;
}

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "primary" | "ghost";
};

export function Button({ variant = "primary", className = "", ...props }: ButtonProps) {
  const base =
    "inline-flex items-center gap-2 text-sm font-medium rounded-btn px-[18px] py-[10px] cursor-pointer border transition-colors focus-visible:outline focus-visible:outline-2 focus-visible:outline-teal focus-visible:outline-offset-2 disabled:opacity-60 disabled:cursor-not-allowed";
  const styles =
    variant === "primary"
      ? "bg-teal text-on-teal border-teal hover:bg-teal-hover hover:border-teal-hover"
      : "bg-transparent text-muted border-line hover:text-ink hover:border-line-strong";
  return <button className={`${base} ${styles} ${className}`} {...props} />;
}

const STATUS_STYLES: Record<string, { label: string; cls: string; dot: string }> = {
  ready: { label: "Works", cls: "text-verified border-verified/40", dot: "bg-verified" },
  building: { label: "Building…", cls: "text-attention border-attention/40", dot: "bg-attention" },
  draft: { label: "Draft", cls: "text-muted border-line-strong", dot: "bg-line-strong" },
  error: { label: "Error", cls: "text-danger border-danger/40", dot: "bg-danger" },
};

export function StatusChip({ status }: { status: ProjectStatus }) {
  const s = STATUS_STYLES[status] ?? STATUS_STYLES.draft;
  return (
    <span
      className={`inline-flex items-center gap-1.5 text-xs font-medium px-[9px] py-[3px] rounded-full border ${s.cls}`}
    >
      <span className={`w-1.5 h-1.5 rounded-full ${s.dot}`} />
      {s.label}
    </span>
  );
}

export function LogoTile({ size = 28 }: { size?: number }) {
  return (
    <span
      className="rounded-[7px] bg-teal flex items-center justify-center flex-none"
      style={{ width: size, height: size }}
    >
      <span
        className="font-display font-semibold text-on-teal"
        style={{ fontSize: size * 0.6, lineHeight: 1 }}
      >
        S
      </span>
    </span>
  );
}

/** Prototype "state" card — used for error / empty / config states. */
export function StateCard({
  icon,
  tone = "muted",
  title,
  children,
  action,
}: {
  icon: string;
  tone?: "error" | "warn" | "muted";
  title: string;
  children: ReactNode;
  action?: ReactNode;
}) {
  const toneCls =
    tone === "error"
      ? "bg-danger/15 text-danger"
      : tone === "warn"
        ? "bg-attention/15 text-attention"
        : "bg-surface-2 text-muted border border-line";
  return (
    // An error card appears because something happened, not because the user
    // clicked — a build stopped, a preview would not build. Announced, so it is
    // not a silent change on a page somebody is not looking at. `alert` for an
    // error because it interrupts; `status` for the rest because it does not.
    <div
      role={tone === "error" ? "alert" : "status"}
      className="bg-surface border border-line rounded-card p-[22px] text-center flex flex-col items-center gap-[9px] max-w-md mx-auto"
    >
      <div className={`w-[42px] h-[42px] rounded-btn flex items-center justify-center text-[19px] ${toneCls}`}>
        {icon}
      </div>
      <h3 className="font-display font-semibold text-base">{title}</h3>
      <p className="text-[13px] text-muted max-w-[40ch] leading-relaxed">{children}</p>
      {action && <div className="mt-1.5">{action}</div>}
    </div>
  );
}
