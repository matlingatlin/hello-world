import type { Response } from "express";

export const KEEPALIVE_MS = 15_000;

/**
 * Open an SSE response that survives a quiet build.
 *
 * A real build says nothing for minutes at a time — Layer B, then Layer C, then
 * the first package — and anything between this process and the browser reads
 * that silence as a dead connection. The engine learned this on its own hop and
 * its fix even names the next one: "every SSE client ignores a comment frame —
 * including proxies, which drop idle connections for the same reason". This hop
 * never got one, so a build behind a forwarding proxy (a Codespace) died with
 * "The build stopped — network error" while the build itself ran happily on.
 *
 * A comment frame every {@link KEEPALIVE_MS} costs nothing and is invisible to
 * the client: EventSource and the app's own parser both drop lines starting `:`.
 */
export function openStream(res: Response): {
  emit: (event: string, data: Record<string, unknown>) => void;
  close: () => void;
} {
  res.setHeader("Content-Type", "text/event-stream");
  res.setHeader("Cache-Control", "no-cache, no-transform");
  res.setHeader("Connection", "keep-alive");
  // Nginx and friends buffer a response until it is "big enough", which for a
  // stream means forever. Belt and braces with no-transform above.
  res.setHeader("X-Accel-Buffering", "no");
  res.flushHeaders?.();

  const beat = setInterval(() => res.write(": keep-alive\n\n"), KEEPALIVE_MS);
  // Unref so a forgotten stream can never hold the process open in tests.
  beat.unref?.();
  const close = () => {
    clearInterval(beat);
    res.end();
  };
  // The client can leave at any time; the build keeps running (that is the
  // promise the build screen makes), but this timer must not outlive them.
  res.on("close", () => clearInterval(beat));

  return {
    emit: (event, data) => {
      res.write(`event: ${event}\ndata: ${JSON.stringify(data)}\n\n`);
    },
    close,
  };
}
