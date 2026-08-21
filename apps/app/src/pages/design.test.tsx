import type { ApplyDesignChangeResponse, DesignPreviewResponse } from "@scio/shared";
import { act, cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";
import { ApiError } from "../lib/api";
import { connectBridge } from "../lib/bridge";
import * as useApiModule from "../lib/useApi";
import { DesignPage } from "./DesignPage";
import { InvolvePage } from "./InvolvePage";

/**
 * The design window, with the API and the preview both faked.
 *
 * What is being checked is the half a person touches, and specifically the two
 * decisions the screen is built on:
 *
 * 1. **The pending list is the change set.** Marking adds a line; the lines are
 *    editable and removable; "Generate again" sends all of them at once.
 * 2. **A conflict is a question, not a build.** Both answers are offered, and
 *    nothing is applied until one of them is given.
 *
 * Plus the honesty property that everything else rests on: a marking the engine
 * cannot address is *named*, never silently dropped and never quietly resolved
 * to the element around it (B039).
 */

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});

const navigate = vi.fn();
vi.mock("react-router-dom", async () => {
  const actual = await vi.importActual<typeof import("react-router-dom")>("react-router-dom");
  return { ...actual, useNavigate: () => navigate };
});

const PREVIEW_ORIGIN = "http://127.0.0.1:41234";

const MANIFEST = {
  elements: {
    "booking-form-submit": {
      package: "pkg_feature_booking",
      file: "components/booking-form.tsx",
      line: 4,
    },
    "booking-list-empty": {
      package: "pkg_feature_booking",
      file: "components/booking-list.tsx",
      line: 4,
    },
  },
};

function preview(overrides: Partial<DesignPreviewResponse> = {}): DesignPreviewResponse {
  return {
    previewUrl: PREVIEW_ORIGIN,
    manifest: MANIFEST,
    designVersion: null,
    whole: "You're building a table-booking app for your guests.",
    summary: "",
    ...overrides,
  };
}

function applied(overrides: Partial<ApplyDesignChangeResponse> = {}): ApplyDesignChangeResponse {
  return {
    applied: true,
    conflicts: [],
    packages: [
      {
        package: "pkg_feature_booking",
        editedFiles: ["components/booking-form.tsx"],
        unchangedFiles: 3,
        isolated: true,
        accepted: true,
        rejection: "",
      },
    ],
    skipped: [],
    previewUrl: PREVIEW_ORIGIN,
    manifest: MANIFEST,
    designVersion: null,
    summary: "",
    ...overrides,
  };
}

function mockApi(overrides: Record<string, unknown> = {}) {
  const api = {
    getDesign: vi.fn().mockResolvedValue(preview()),
    streamDesignPreview: vi.fn().mockResolvedValue(undefined),
    applyDesignChange: vi.fn().mockResolvedValue(applied()),
    listDesignVersions: vi.fn().mockResolvedValue({ designVersions: [] }),
    restoreDesignVersion: vi.fn().mockResolvedValue({
      restored: true,
      previewUrl: PREVIEW_ORIGIN,
      manifest: MANIFEST,
      designVersion: null,
      error: "",
    }),
    amendSpec: vi.fn().mockResolvedValue({
      specVersion: { id: "s2", number: 2, isCurrent: true, createdAt: "2026-08-19T00:00:00Z" },
      allowances: [],
      removedNonGoal: null,
    }),
    ...overrides,
  };
  vi.spyOn(useApiModule, "useApi").mockReturnValue(api as never);
  return api;
}

/** A message from the preview, as the in-iframe bridge would post it. */
function fromPreview(body: Record<string, unknown>, origin = PREVIEW_ORIGIN) {
  fireEvent(
    window,
    new MessageEvent("message", { data: { source: "scio-preview", ...body }, origin }),
  );
}

function mark(scioId: string | null, extra: Record<string, unknown> = {}) {
  fromPreview({
    type: "marked",
    hit: {
      scio_id: scioId,
      scio_package: scioId ? "pkg_feature_booking" : null,
      tag: "button",
      text: scioId ? "Book a table" : "some text",
      ancestor_id: null,
      ancestor_package: null,
      ancestor_distance: 0,
      ...extra,
    },
    coords: { x: 10, y: 20, scroll_y: 0 },
    route: "/booking/new",
  });
}

function renderPage() {
  return render(
    <MemoryRouter initialEntries={["/projects/p1/design"]}>
      <Routes>
        <Route path="/projects/:projectId/design" element={<DesignPage />} />
      </Routes>
    </MemoryRouter>,
  );
}

/** Wait for the preview to be embedded — everything else happens after that. */
async function ready() {
  await screen.findByTitle("Your app");
  // The iframe existing is not the same as the page listening. The marking
  // bridge is attached in an effect, and `mark()` below fires a window message
  // SYNCHRONOUSLY — so without flushing effects first, a message can arrive
  // before the listener does and simply vanish. That is what made this file
  // flaky: it passed on an idle machine and failed under a loaded one, where
  // effect flushing lags the test's own synchronous calls (B105).
  await act(async () => {});
}

describe("The design window", () => {
  it("embeds the preview it was given, and says what is being built", async () => {
    mockApi();
    renderPage();

    const frame = (await screen.findByTitle("Your app")) as HTMLIFrameElement;
    expect(frame.src.startsWith(PREVIEW_ORIGIN)).toBe(true);
    expect(screen.getByText(/table-booking app/)).toBeDefined();
  });

  it("builds a preview when there isn't one, showing real per-part progress", async () => {
    const stream = vi.fn(
      async (_id: string, onEvent: (e: string, d: Record<string, unknown>) => void) => {
        onEvent("progress", {
          package_id: "pkg_foundation",
          status: "passed",
          message: "pkg_foundation: works — 4/4 checks passed.",
        });
        onEvent("finished", { app_url: PREVIEW_ORIGIN, manifest: MANIFEST, whole: "" });
      },
    );
    mockApi({
      getDesign: vi.fn().mockResolvedValue(preview({ previewUrl: null, manifest: null })),
      streamDesignPreview: stream,
    });
    renderPage();

    expect(await screen.findByTitle("Your app")).toBeDefined();
    expect(stream).toHaveBeenCalled();
  });

  it("adds a marking to the change set, resolved to its package", async () => {
    mockApi();
    renderPage();
    await ready();

    mark("booking-form-submit");

    expect(await screen.findByText("Book a table")).toBeDefined();
    expect(screen.getByText(/feature booking · components\/booking-form.tsx:4/)).toBeDefined();
  });

  it("names a marking it cannot address instead of dropping it", async () => {
    mockApi();
    renderPage();
    await ready();

    mark(null, { ancestor_id: "booking-form" });

    const named = await screen.findByTestId("unaddressable");
    expect(named.textContent).toContain("no marker of its own");
    // The ancestor is evidence for the refusal, never a substitute target.
    expect(named.textContent).toContain("booking-form");
  });

  it("ignores a message that did not come from the preview's origin", async () => {
    mockApi();
    renderPage();
    await ready();

    fromPreview(
      {
        type: "marked",
        hit: { scio_id: "booking-form-submit", tag: "button", text: "Book a table" },
        coords: { x: 0, y: 0, scroll_y: 0 },
        route: "/",
      },
      "http://evil.example",
    );

    expect(screen.queryByText("Book a table")).toBeNull();
    expect(screen.getByText(/click the preview to add a change/)).toBeDefined();
  });

  it("removes a change from the set", async () => {
    const user = userEvent.setup();
    mockApi();
    renderPage();
    await ready();

    mark("booking-form-submit");
    await screen.findByText("Book a table");
    await user.click(screen.getByLabelText("Remove change 1"));

    expect(screen.queryByText("Book a table")).toBeNull();
  });

  it("sends every pending marking plus the prompt as ONE change", async () => {
    const user = userEvent.setup();
    const api = mockApi();
    renderPage();
    await ready();

    mark("booking-form-submit");
    mark("booking-list-empty");
    await screen.findByLabelText("Note for change 2");

    await user.type(screen.getByLabelText("Note for change 1"), "say Reserve");
    await user.type(screen.getByLabelText("Note for change 2"), "say Nothing booked");
    await user.type(screen.getByLabelText("Anything else"), "warmer colours");
    await user.click(screen.getByRole("button", { name: "Generate again" }));

    await waitFor(() => expect(api.applyDesignChange).toHaveBeenCalledTimes(1));
    const [, body] = api.applyDesignChange.mock.calls[0];
    expect(body.markings.map((m: { scioId: string }) => m.scioId)).toEqual([
      "booking-form-submit",
      "booking-list-empty",
    ]);
    expect(body.markings.map((m: { note: string }) => m.note)).toEqual([
      "say Reserve",
      "say Nothing booked",
    ]);
    expect(body.prompt).toBe("warmer colours");
  });

  it("clears the change set on success and shows the isolation proof", async () => {
    const user = userEvent.setup();
    mockApi();
    renderPage();
    await ready();

    mark("booking-form-submit");
    await screen.findByText("Book a table");
    await user.click(screen.getByRole("button", { name: "Generate again" }));

    const outcome = await screen.findByTestId("outcome");
    expect(outcome.textContent).toContain("components/booking-form.tsx");
    expect(outcome.textContent).toContain("3 other files untouched");
    expect(screen.queryByLabelText("Note for change 1")).toBeNull();
  });

  it("keeps a marking the engine skipped, and says why", async () => {
    const user = userEvent.setup();
    mockApi({
      applyDesignChange: vi.fn().mockResolvedValue(
        applied({
          skipped: [
            { scioId: "booking-form-submit", note: "say Reserve", error: "not in the manifest" },
          ],
        }),
      ),
    });
    renderPage();
    await ready();

    mark("booking-form-submit");
    await screen.findByText("Book a table");
    await user.click(screen.getByRole("button", { name: "Generate again" }));

    const outcome = await screen.findByTestId("outcome");
    expect(outcome.textContent).toContain("not in the manifest");
    // Still there, so it can be reworded rather than lost.
    expect(screen.getByLabelText("Note for change 1")).toBeDefined();
  });
});

describe("A conflict with the approved spec", () => {
  const nonGoal = {
    kind: "non_goal",
    scioId: "booking-form-submit",
    note: "add card payment here",
    specSays: "no payments for now",
    question: "This asks to add something you deliberately left out: “no payments for now”.",
  };
  const access = {
    kind: "access",
    scioId: "booking-list-empty",
    note: "make the bookings public",
    specSays: "personal data, with row-level security on",
    question: "This asks to open up data the spec marked as sensitive.",
  };

  it("is shown as a question, with nothing built", async () => {
    const user = userEvent.setup();
    mockApi({
      applyDesignChange: vi
        .fn()
        .mockResolvedValue(applied({ applied: false, conflicts: [nonGoal], packages: [] })),
    });
    renderPage();
    await ready();

    mark("booking-form-submit");
    await screen.findByText("Book a table");
    await user.click(screen.getByRole("button", { name: "Generate again" }));

    const block = await screen.findByTestId("conflicts");
    expect(block.textContent).toContain("nothing was built");
    expect(block.textContent).toContain("no payments for now");
    expect(screen.getByRole("button", { name: "Keep it as-is" })).toBeDefined();
    expect(screen.getByRole("button", { name: "Change the plan" })).toBeDefined();
    expect(screen.queryByTestId("outcome")).toBeNull();
  });

  it("'Keep it as-is' drops that marking and builds nothing", async () => {
    const user = userEvent.setup();
    const api = mockApi({
      applyDesignChange: vi
        .fn()
        .mockResolvedValue(applied({ applied: false, conflicts: [nonGoal], packages: [] })),
    });
    renderPage();
    await ready();

    mark("booking-form-submit");
    await screen.findByText("Book a table");
    await user.click(screen.getByRole("button", { name: "Generate again" }));
    await screen.findByTestId("conflicts");
    await user.click(screen.getByRole("button", { name: "Keep it as-is" }));

    expect(screen.queryByTestId("conflicts")).toBeNull();
    expect(screen.queryByText("Book a table")).toBeNull();
    expect(api.applyDesignChange).toHaveBeenCalledTimes(1);
    expect(api.amendSpec).not.toHaveBeenCalled();
  });

  it("'Change the plan' amends the spec, then applies", async () => {
    const user = userEvent.setup();
    const change = vi
      .fn()
      .mockResolvedValueOnce(applied({ applied: false, conflicts: [nonGoal], packages: [] }))
      .mockResolvedValueOnce(applied());
    const api = mockApi({ applyDesignChange: change });
    renderPage();
    await ready();

    mark("booking-form-submit");
    await screen.findByText("Book a table");
    await user.click(screen.getByRole("button", { name: "Generate again" }));
    await screen.findByTestId("conflicts");
    await user.click(screen.getByRole("button", { name: "Change the plan" }));

    await waitFor(() => expect(api.amendSpec).toHaveBeenCalledTimes(1));
    expect(api.amendSpec.mock.calls[0][1]).toMatchObject({
      kind: "non_goal",
      specSays: "no payments for now",
    });
    await waitFor(() => expect(change).toHaveBeenCalledTimes(2));
    expect(await screen.findByTestId("outcome")).toBeDefined();
  });

  it("asks a second time before dropping a protection, and names it", async () => {
    const user = userEvent.setup();
    const api = mockApi({
      applyDesignChange: vi
        .fn()
        .mockResolvedValue(applied({ applied: false, conflicts: [access], packages: [] })),
    });
    renderPage();
    await ready();

    mark("booking-list-empty");
    await screen.findByText("Book a table");
    await user.click(screen.getByRole("button", { name: "Generate again" }));
    await screen.findByTestId("conflicts");
    await user.click(screen.getByRole("button", { name: "Change the plan" }));

    // Not yet: a security decision is confirmed on its own terms first.
    expect(api.amendSpec).not.toHaveBeenCalled();
    expect(screen.getByText(/drops a protection Scio worked out for you/)).toBeDefined();

    await user.click(screen.getByRole("button", { name: "Yes, allow it" }));
    await waitFor(() => expect(api.amendSpec).toHaveBeenCalledTimes(1));
    expect(api.amendSpec.mock.calls[0][1]).toMatchObject({ kind: "access" });
  });
});

describe("Versions", () => {
  const version = (number: number, ref: Record<string, unknown>, isCurrent = false) => ({
    id: `d${number}`,
    projectId: "p1",
    number,
    ref: JSON.stringify(ref),
    isCurrent,
    createdAt: "2026-08-19T00:00:00Z",
  });

  it("offers a way back to a version that was committed", async () => {
    const user = userEvent.setup();
    const api = mockApi({
      listDesignVersions: vi.fn().mockResolvedValue({
        designVersions: [
          version(2, { change: "say Reserve", gitSha: "bbb" }, true),
          version(1, { change: "the first preview", gitSha: "aaa" }),
        ],
      }),
    });
    renderPage();
    await ready();

    const panel = await screen.findByTestId("versions");
    expect(panel.textContent).toContain("the first preview");
    await user.click(screen.getByRole("button", { name: "Return to this version" }));

    await waitFor(() => expect(api.restoreDesignVersion).toHaveBeenCalledWith("p1", "d1"));
  });

  it("does not offer a way back to one that was never committed", async () => {
    mockApi({
      listDesignVersions: vi.fn().mockResolvedValue({
        designVersions: [
          version(2, { change: "say Reserve", gitSha: "bbb" }, true),
          version(1, { change: "the first preview" }),
        ],
      }),
    });
    renderPage();
    await ready();

    await screen.findByTestId("versions");
    expect(screen.queryByRole("button", { name: "Return to this version" })).toBeNull();
  });

  it("says why a version could not be restored, rather than looking broken", async () => {
    const user = userEvent.setup();
    mockApi({
      listDesignVersions: vi.fn().mockResolvedValue({
        designVersions: [
          version(2, { change: "say Reserve", gitSha: "bbb" }, true),
          version(1, { change: "the first preview", gitSha: "aaa" }),
        ],
      }),
      restoreDesignVersion: vi.fn().mockResolvedValue({
        restored: false,
        previewUrl: PREVIEW_ORIGIN,
        manifest: MANIFEST,
        designVersion: null,
        error: "that version's code no longer matches its instrumentation",
      }),
    });
    renderPage();
    await ready();

    await screen.findByTestId("versions");
    await user.click(screen.getByRole("button", { name: "Return to this version" }));

    expect(await screen.findByText(/no longer matches its instrumentation/)).toBeDefined();
  });
});

describe("The bridge", () => {
  it("never posts to a wildcard origin", () => {
    const post = vi.fn();
    const bridge = connectBridge(() => ({ postMessage: post }) as never, PREVIEW_ORIGIN, {});

    bridge.arm(true);
    bridge.ping();

    expect(post).toHaveBeenCalledTimes(2);
    for (const [, origin] of post.mock.calls) expect(origin).toBe(PREVIEW_ORIGIN);
    bridge.stop();
  });

  it("says nothing at all when the preview URL is not one it can post to", () => {
    const post = vi.fn();
    const bridge = connectBridge(() => ({ postMessage: post }) as never, "not a url", {});

    bridge.arm(true);

    expect(post).not.toHaveBeenCalled();
    bridge.stop();
  });
});

describe("The involvement question", () => {
  it("offers both paths, and each goes where it says", async () => {
    const user = userEvent.setup();
    render(
      <MemoryRouter initialEntries={["/projects/p1/involve"]}>
        <Routes>
          <Route path="/projects/:projectId/involve" element={<InvolvePage />} />
        </Routes>
      </MemoryRouter>,
    );

    await user.click(screen.getByText("Just build it"));
    expect(navigate).toHaveBeenCalledWith("/projects/p1/build");

    await user.click(screen.getByText("Shape the design first"));
    expect(navigate).toHaveBeenCalledWith("/projects/p1/design");
  });
});

describe("A preview that stopped running", () => {
  /**
   * The component waits a real five seconds before deciding a preview is gone
   * (DesignPage: the countdown starts at the iframe's `load`, because a dev
   * preview compiles on first request). This test used to wait it out with an
   * 8-second margin, which held on an idle machine and did not under load: the
   * whole suite runs in parallel workers, and a starved worker turned a
   * comfortable 3-second margin into a failure. That is what made the suite
   * flaky — two different tests failed on two runs and three later runs were
   * clean (B105).
   *
   * Fake timers instead. The behaviour under test is "after five seconds with
   * no word from the bridge, say so", and a test of that should ADVANCE time,
   * never wait for it. The suite also gets five seconds shorter.
   */
  it("offers a way to build it again rather than a dead frame", async () => {
    const user = userEvent.setup();
    const stream = vi.fn().mockResolvedValue(undefined);
    mockApi({ streamDesignPreview: stream });
    renderPage();

    // Real timers until the frame is here: `findBy*` polls, and a fake clock
    // that nobody advances would hang it.
    const frame = (await screen.findByTitle("Your app")) as HTMLIFrameElement;

    vi.useFakeTimers();
    // The iframe loads (or fails to), and the bridge never says hello.
    fireEvent.load(frame);
    act(() => {
      vi.advanceTimersByTime(5000);
    });
    vi.useRealTimers();

    const notice = screen.getByTestId("bridge-unreachable");
    expect(notice.textContent).toContain("isn't running any more");

    await user.click(screen.getByRole("button", { name: "Build the preview again" }));
    expect(stream).toHaveBeenCalledWith("p1", expect.any(Function));
  });
});

describe("A connection that stopped, and a preview that did not", () => {
  it("does not report a dropped stream as a preview that could not be built", async () => {
    mockApi({
      getDesign: vi.fn().mockResolvedValue(preview({ previewUrl: null })),
      streamDesignPreview: vi.fn().mockRejectedValue(new ApiError(0, "the connection dropped")),
    });
    renderPage();

    expect(await screen.findByText("We lost the connection")).toBeDefined();
  });

  it("shows the preview that finished while the page was deaf", async () => {
    const getDesign = vi
      .fn()
      .mockResolvedValueOnce(preview({ previewUrl: null }))
      .mockResolvedValue(preview());
    mockApi({
      getDesign,
      streamDesignPreview: vi.fn().mockRejectedValue(new ApiError(0, "the connection dropped")),
    });
    renderPage();

    await userEvent.click(await screen.findByText("Check on it"));

    expect(await screen.findByTitle("Your app")).toBeDefined();
  });

  it("still reports a real preview failure as a failure", async () => {
    mockApi({
      getDesign: vi.fn().mockRejectedValue(new ApiError(409, "Approve a spec first.")),
    });
    renderPage();

    expect(await screen.findByText("Approve a spec first.")).toBeDefined();
    expect(screen.queryByText("We lost the connection")).toBeNull();
  });
});
