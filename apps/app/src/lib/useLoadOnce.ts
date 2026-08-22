import { useEffect, useRef } from "react";

/**
 * Run a load exactly once per key — including across StrictMode's double mount.
 *
 * React 18's StrictMode mounts, unmounts and remounts every component in
 * development, so a plain `useEffect(load, [load])` fetches twice on every page
 * load. That is free today for `/intake`, because the whole and the estimate are
 * stored rather than recomputed (B071) — but it was not free before that, where
 * the second fetch was a second Layer B + Layer C model call, and it doubled the
 * cost of merely opening the wizard (B075).
 *
 * Keyed rather than a bare "did this run" flag: the point is one load per thing
 * being loaded, so navigating to another project still loads that project.
 * Reloading the same key on purpose — a retry button — is a direct call, which
 * is what a deliberate reload should look like.
 */
export function useLoadOnce(key: string, load: () => void): void {
  const loaded = useRef<string | null>(null);
  useEffect(() => {
    if (loaded.current === key) return;
    loaded.current = key;
    load();
    // `load` is deliberately not a trigger: it changes identity whenever the
    // api client does, and re-running on that would be the double fetch again.
  }, [key, load]);
}
