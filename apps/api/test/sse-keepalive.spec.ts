import { describe, expect, it, vi } from "vitest";
import { KEEPALIVE_MS, openStream } from "../src/common/sse";

/**
 * A real build is silent for minutes. Anything between this process and the
 * browser reads silence as a dead connection — a Codespace's port forwarder
 * did exactly that, and the build screen said "The build stopped — network
 * error" about a build that ran to completion server-side.
 */
function fakeResponse() {
  const written: string[] = [];
  const handlers: Record<string, () => void> = {};
  return {
    written,
    fire: (event: string) => handlers[event]?.(),
    res: {
      setHeader: vi.fn(),
      flushHeaders: vi.fn(),
      write: (chunk: string) => written.push(chunk),
      end: vi.fn(),
      on: (event: string, handler: () => void) => {
        handlers[event] = handler;
      },
    },
  };
}

describe("an SSE stream that survives a quiet build", () => {
  it("sends a comment frame while nothing else is happening", () => {
    vi.useFakeTimers();
    const { res, written } = fakeResponse();

    openStream(res as never);
    expect(written).toEqual([]);

    vi.advanceTimersByTime(KEEPALIVE_MS * 3);
    expect(written).toEqual([": keep-alive\n\n", ": keep-alive\n\n", ": keep-alive\n\n"]);
    vi.useRealTimers();
  });

  it("stops beating once the stream is closed", () => {
    vi.useFakeTimers();
    const { res, written } = fakeResponse();

    const { close } = openStream(res as never);
    close();
    vi.advanceTimersByTime(KEEPALIVE_MS * 5);

    expect(written).toEqual([]);
    expect(res.end).toHaveBeenCalled();
    vi.useRealTimers();
  });

  it("stops beating when the client leaves, without ending the build", () => {
    vi.useFakeTimers();
    const { res, written, fire } = fakeResponse();

    openStream(res as never);
    fire("close");
    vi.advanceTimersByTime(KEEPALIVE_MS * 5);

    expect(written).toEqual([]);
    vi.useRealTimers();
  });

  it("writes events in the shape the app parses", () => {
    const { res, written } = fakeResponse();

    const { emit } = openStream(res as never);
    emit("progress", { message: "foundation" });

    expect(written).toEqual(['event: progress\ndata: {"message":"foundation"}\n\n']);
  });
});
