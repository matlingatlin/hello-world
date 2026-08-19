/**
 * The design window's half of the marking bridge.
 *
 * The preview runs on its own origin, so the window cannot read its DOM —
 * `contentDocument` throws. Everything it knows about what the user marked
 * arrives as a `postMessage` from the script the engine injects into a preview
 * build (`apps/engine/src/scio_engine/builder/preview/bridge.js`).
 *
 * Three rules, all of them from the spike (spikes/design-marking/FINDINGS.md):
 *
 * 1. **Origins are pinned in both directions.** Messages are ignored unless
 *    they came from the preview's own origin, and nothing is ever posted to
 *    `"*"` — that would hand the app's structure to any page that framed it.
 * 2. **It reports, it never decides.** A hit carries both the marked element
 *    and its nearest instrumented ancestor, and the ancestor is evidence for a
 *    refusal, never a substitute target. Resolution is the engine's strict
 *    resolver's job (B039).
 * 3. **It returns data and renders nothing.** The spike's own shell turned a
 *    refusal containing `<div>` into an actual div by putting it through
 *    `innerHTML`. Here the values go into React, which escapes by construction —
 *    so this module must never grow a rendering path.
 */

/** What the in-preview bridge reports about one element. Shape: core.resolver.ElementHit. */
export interface BridgeHit {
  scio_id: string | null;
  scio_package: string | null;
  tag: string;
  text: string;
  ancestor_id: string | null;
  ancestor_package: string | null;
  ancestor_distance: number;
}

export interface BridgeMarked {
  hit: BridgeHit;
  coords: { x: number; y: number; scroll_y: number };
  route: string;
}

/** The bridge announcing itself, with the ids this route actually has. */
export interface BridgeReady {
  route: string;
  ids: string[];
}

export interface BridgeHandlers {
  onReady?: (ready: BridgeReady) => void;
  onMarked?: (marked: BridgeMarked) => void;
}

const SHELL = "scio-shell";
const PREVIEW = "scio-preview";

/**
 * The origin of a preview URL, or "" if it is not one we can post to.
 *
 * Resolved with no base on purpose. A preview always has an absolute URL of its
 * own; resolving a relative or malformed one against `window.location` would
 * silently produce the design window's OWN origin, and the window would then
 * post the app's structure to itself and look merely unresponsive.
 */
export function originOf(previewUrl: string): string {
  try {
    return new URL(previewUrl).origin;
  } catch {
    return "";
  }
}

export interface Bridge {
  /** Turn marking on or off inside the preview. */
  arm: (on: boolean) => void;
  /** Remove the numbered boxes the preview drew. */
  clearMarks: () => void;
  /** Ask the bridge to announce itself again — used after the iframe reloads. */
  ping: () => void;
  /** Stop listening. Safe to call twice. */
  stop: () => void;
}

/**
 * Listen to one preview, and talk back to it.
 *
 * `frame` is read lazily rather than captured: the design window re-points the
 * iframe after every applied change, and a captured `contentWindow` would be
 * the dead one from before the reload.
 */
export function connectBridge(
  frame: () => Window | null,
  previewUrl: string,
  handlers: BridgeHandlers,
): Bridge {
  const origin = originOf(previewUrl);

  function onMessage(event: MessageEvent) {
    // Pinned: a message from anywhere else is not from our preview, whatever
    // it claims in its body.
    if (!origin || event.origin !== origin) return;
    const data = event.data as { source?: string; type?: string } | null;
    if (!data || data.source !== PREVIEW) return;
    if (data.type === "ready") handlers.onReady?.(data as unknown as BridgeReady);
    if (data.type === "marked") handlers.onMarked?.(data as unknown as BridgeMarked);
  }

  window.addEventListener("message", onMessage);

  function send(type: string, extra: Record<string, unknown> = {}) {
    if (!origin) return;
    frame()?.postMessage({ source: SHELL, type, ...extra }, origin);
  }

  return {
    arm: (on: boolean) => send("arm", { on }),
    clearMarks: () => send("clear"),
    ping: () => send("ping"),
    stop: () => window.removeEventListener("message", onMessage),
  };
}
