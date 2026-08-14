import type { ReactNode } from "react";

/**
 * What a list says when it has nothing. An empty screen that explains itself is
 * the difference between "new" and "broken".
 */
export function UiEmptyState({ title, children }: { title: string; children?: ReactNode }) {
  return (
    <div className="flex flex-col items-center gap-2 rounded-[__TOKEN_RADIUS__] border border-dashed p-8 text-center">
      <p className="font-medium">{title}</p>
      {children ? <div className="text-sm opacity-70">{children}</div> : null}
    </div>
  );
}
