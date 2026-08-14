import type { InputHTMLAttributes } from "react";

/**
 * A labelled input. The label is bound to the control, so the field is usable
 * with a screen reader and a keyboard without anyone remembering to do it.
 */
export function UiField({
  label,
  hint,
  ...props
}: InputHTMLAttributes<HTMLInputElement> & { label: string; hint?: string }) {
  return (
    <label className="flex flex-col gap-1 text-sm">
      {label}
      <input {...props} className="rounded-[__TOKEN_RADIUS__] border px-3 py-2" />
      {hint ? <span className="text-xs opacity-70">{hint}</span> : null}
    </label>
  );
}
