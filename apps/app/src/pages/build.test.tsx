import type { LatestBuildResponse } from "@scio/shared";
import { cleanup, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";
import { ApiError } from "../lib/api";
import * as useApiModule from "../lib/useApi";
import { BuildPage } from "./BuildPage";
import { RevealPage } from "./RevealPage";
import { ShipPage } from "./ShipPage";

/**
 * The build view and the reveal, with the API mocked.
 *
 * Two claims are being checked, and they are the two the product is staking its
 * credibility on: progress is real (it comes from parts finishing, not a timer),
 * and the reveal tells the truth (what needs a look is as visible as what works).
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

const STARTED = {
  project_id: "p1",
  whole: "You're building a table-booking app for your guests.",
  packages: ["pkg_foundation", "pkg_schema", "pkg_feature_booking"],
  total: 3,
  workspace: "/tmp/p1",
};

function progress(id: string, done: number, status: string, message: string) {
  return { package_id: id, index: done, total: 3, done, status, message };
}

const HONEST: LatestBuildResponse["honestStatus"] = {
  works: false,
  summary: "2 of 3 parts work. 1 need a look.",
  working: ["pkg_foundation", "pkg_schema"],
  needs_look: ["pkg_feature_booking"],
  blocked: [],
  failed: [],
  remainders: ["pkg_feature_booking: needs a look — the form has no date field"],
  standin: false,
};

function latest(overrides: Partial<LatestBuildResponse> = {}): LatestBuildResponse {
  return {
    buildVersion: {
      id: "b1",
      number: 1,
      description: "2 of 3 parts work.",
      gitSha: "3a28a30d9de2aaaa",
      isCurrent: true,
      createdAt: "2026-08-12T00:00:00Z",
    },
    previewUrl: "http://127.0.0.1:41234",
    projectStatus: "ready",
    honestStatus: HONEST,
    whole: "You're building a table-booking app for your guests.",
    ...overrides,
  };
}

function mockApi(overrides: Record<string, unknown>) {
  const api = {
    streamBuild: vi.fn().mockResolvedValue(undefined),
    latestBuild: vi.fn().mockResolvedValue(latest()),
    ...overrides,
  };
  vi.spyOn(useApiModule, "useApi").mockReturnValue(api as never);
  return api;
}

/** A streamBuild that replays a scripted event sequence, like the API does. */
function scriptedStream(events: Array<[string, Record<string, unknown>]>) {
  return vi.fn(
    async (_projectId: string, onEvent: (frame: { event: string; data: unknown }) => void) => {
      for (const [event, data] of events) onEvent({ event, data });
    },
  );
}

function renderAt(path: string, element: JSX.Element) {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <Routes>
        <Route path="/projects/:projectId/build" element={element} />
        <Route path="/projects/:projectId/reveal" element={element} />
        <Route path="/projects/:projectId/ship" element={element} />
      </Routes>
    </MemoryRouter>,
  );
}

describe("Build view", () => {
  it("draws the real schedule from the engine's plan", async () => {
    mockApi({ streamBuild: scriptedStream([["started", STARTED]]) });
    renderAt("/projects/p1/build", <BuildPage />);

    expect(await screen.findByText("foundation")).toBeDefined();
    expect(screen.getByText("schema")).toBeDefined();
    expect(screen.getByText("booking")).toBeDefined();
    expect(screen.getByText("0 of 3 parts done")).toBeDefined();
  });

  it("ticks parts off as they actually finish", async () => {
    mockApi({
      streamBuild: scriptedStream([
        ["started", STARTED],
        ["progress", progress("pkg_foundation", 0, "building", "Building pkg_foundation")],
        ["progress", progress("pkg_foundation", 1, "passed", "pkg_foundation: works — 4/4 checks passed.")],
        ["progress", progress("pkg_schema", 2, "passed", "pkg_schema: works — 4/4 checks passed.")],
      ]),
    });
    renderAt("/projects/p1/build", <BuildPage />);

    expect(await screen.findByText("2 of 3 parts done")).toBeDefined();
    // The log shows what happened, in the engine's own words.
    expect(screen.getByText(/pkg_foundation: works — 4\/4 checks passed./)).toBeDefined();
  });

  it("shows a part that needs a look as such, mid-build", async () => {
    mockApi({
      streamBuild: scriptedStream([
        ["started", STARTED],
        [
          "progress",
          progress("pkg_feature_booking", 1, "needs_look", "pkg_feature_booking: needs a look — no date field"),
        ],
      ]),
    });
    renderAt("/projects/p1/build", <BuildPage />);

    expect(await screen.findByText(/needs a look — no date field/)).toBeDefined();
  });

  it("goes to the reveal when the build finishes", async () => {
    mockApi({
      streamBuild: scriptedStream([
        ["started", STARTED],
        ["finished", { project_id: "p1", app_url: "http://127.0.0.1:41234" }],
      ]),
    });
    renderAt("/projects/p1/build", <BuildPage />);

    await waitFor(() => expect(navigate).toHaveBeenCalledWith("/projects/p1/reveal"));
  });

  it("shows a build error where the progress was", async () => {
    mockApi({
      streamBuild: scriptedStream([
        ["error", { type: "workspace_unavailable", message: "No app scaffold available." }],
      ]),
    });
    renderAt("/projects/p1/build", <BuildPage />);

    expect(await screen.findByText("No app scaffold available.")).toBeDefined();
    expect(screen.getByText("The build stopped")).toBeDefined();
  });

  it("calls a dropped connection what it is, not a stopped build", async () => {
    // The lede on this very screen promises the build keeps running when you
    // leave it. "The build stopped" contradicted that every time the stream
    // died, and it was never once true: the api had no failure to report.
    mockApi({
      streamBuild: vi.fn().mockRejectedValue(new ApiError(0, "the connection dropped")),
    });
    renderAt("/projects/p1/build", <BuildPage />);

    expect(await screen.findByText("We lost the connection")).toBeDefined();
    expect(screen.queryByText("The build stopped")).toBeNull();
  });

  it("goes to the reveal if the build finished while the page was deaf", async () => {
    mockApi({
      streamBuild: vi.fn().mockRejectedValue(new ApiError(0, "the connection dropped")),
    });
    renderAt("/projects/p1/build", <BuildPage />);

    await userEvent.click(await screen.findByText("Check on it"));

    await waitFor(() => expect(navigate).toHaveBeenCalledWith("/projects/p1/reveal"));
  });

  it("still reports a real build failure as a failure", async () => {
    mockApi({
      streamBuild: vi.fn().mockRejectedValue(new ApiError(409, "Approve a spec first.")),
    });
    renderAt("/projects/p1/build", <BuildPage />);

    expect(await screen.findByText("Approve a spec first.")).toBeDefined();
    expect(screen.queryByText("We lost the connection")).toBeNull();
  });

  it("tells the user they can leave", async () => {
    mockApi({ streamBuild: scriptedStream([["started", STARTED]]) });
    renderAt("/projects/p1/build", <BuildPage />);

    expect(await screen.findByText(/You can leave this page/)).toBeDefined();
  });
});

describe("Reveal", () => {
  it("puts what the build spent next to what it was estimated at", async () => {
    // An estimate alone is a promise; a spend alone is a number with nothing to
    // judge it by. Together, an estimate becomes something you can trust the
    // second time — or knowingly distrust. The first real build spent $2.69
    // against an estimate topping out at $2.51.
    mockApi({
      latestBuild: vi.fn().mockResolvedValue(
        latest({
          estimate: { parts: 7, cost_usd: { low: 1.05, high: 2.51 }, minutes: { low: 14, high: 33 } },
          spend: { costUsd: 2.688465, tokens: 248952, model: "claude-sonnet-5", at: "2026-08-20T01:22:34Z" },
        } as never),
      ),
    });
    renderAt("/projects/p1/reveal", <RevealPage />);

    const line = await screen.findByTestId("build-provenance");
    expect(line.textContent).toContain("estimated ~$1.05–$2.51");
    expect(line.textContent).toContain("$2.69 spent");
    expect(line.textContent).toContain("249k tokens");
  });

  it("shows the spend alone rather than inventing an estimate to compare it to", async () => {
    mockApi({
      latestBuild: vi.fn().mockResolvedValue(
        latest({
          spend: { costUsd: 0.42, tokens: 1200, model: "claude-sonnet-5", at: "2026-08-20T01:22:34Z" },
        } as never),
      ),
    });
    renderAt("/projects/p1/reveal", <RevealPage />);

    const line = await screen.findByTestId("build-provenance");
    expect(line.textContent).toContain("$0.42 spent");
    expect(line.textContent).not.toContain("estimated");
  });

  it("embeds the running app", async () => {
    mockApi({});
    renderAt("/projects/p1/reveal", <RevealPage />);

    const frame = (await screen.findByTitle("Your app")) as HTMLIFrameElement;
    expect(frame.src).toBe("http://127.0.0.1:41234/");
  });

  it("shows what needs a look as prominently as what works", async () => {
    mockApi({});
    renderAt("/projects/p1/reveal", <RevealPage />);

    expect(await screen.findByText(/Works \(2\)/)).toBeDefined();
    expect(screen.getByText(/Needs a look \(1\)/)).toBeDefined();
    expect(screen.getByText(/the form has no date field/)).toBeDefined();
    // The headline does not claim more than the build earned.
    expect(screen.getByText(/with a few notes/)).toBeDefined();
  });

  it("says so plainly when everything worked", async () => {
    mockApi({
      latestBuild: vi.fn().mockResolvedValue(
        latest({
          honestStatus: {
            ...HONEST,
            works: true,
            summary: "3 of 3 parts work.",
            needs_look: [],
            remainders: [],
          },
        }),
      ),
    });
    renderAt("/projects/p1/reveal", <RevealPage />);

    expect(await screen.findByText("Here's your app")).toBeDefined();
    expect(screen.queryByText(/Needs a look/)).toBeNull();
  });

  it("shows blocked parts rather than omitting them", async () => {
    mockApi({
      latestBuild: vi.fn().mockResolvedValue(
        latest({
          honestStatus: { ...HONEST, blocked: ["pkg_feature_menu"], works: false },
        }),
      ),
    });
    renderAt("/projects/p1/reveal", <RevealPage />);

    expect(await screen.findByText(/Not built \(1\)/)).toBeDefined();
    expect(screen.getByText("pkg_feature_menu")).toBeDefined();
  });

  it("admits when the code came from the stand-in builder", async () => {
    mockApi({
      latestBuild: vi.fn().mockResolvedValue(
        latest({ honestStatus: { ...HONEST, standin: true } }),
      ),
    });
    renderAt("/projects/p1/reveal", <RevealPage />);

    expect(await screen.findByText(/stand-in builder/)).toBeDefined();
    expect(screen.getByText(/the code inside is placeholder/)).toBeDefined();
  });

  it("shows what you built, and the version it came from", async () => {
    mockApi({});
    renderAt("/projects/p1/reveal", <RevealPage />);

    expect(await screen.findByText(/What you built/)).toBeDefined();
    expect(screen.getByText(/version 1 · 3a28a30d9de2/)).toBeDefined();
  });

  it("says the preview isn't running rather than showing an empty frame", async () => {
    mockApi({ latestBuild: vi.fn().mockResolvedValue(latest({ previewUrl: null })) });
    renderAt("/projects/p1/reveal", <RevealPage />);

    expect(await screen.findByText(/isn't running right now/)).toBeDefined();
    expect(screen.queryByTitle("Your app")).toBeNull();
  });

  it("sends 'Open & refine' to the design window, which is where refining happens", async () => {
    // It used to lead to a placeholder that said it was being ported. Since a
    // delivery build promotes the design workspace rather than rebuilding it
    // (ADR-0017), the app you shaped and the app you were given are the same
    // files — so the button has had somewhere real to go for a while.
    mockApi({});
    renderAt("/projects/p1/reveal", <RevealPage />);

    await userEvent.click(await screen.findByRole("button", { name: /Open & refine/ }));
    expect(navigate).toHaveBeenCalledWith("/projects/p1/design");
  });

  it("says publishing is not built rather than offering a button that isn't", async () => {
    mockApi({});
    renderAt("/projects/p1/reveal", <RevealPage />);

    expect(await screen.findByText(/Publishing your app somewhere permanent isn't built yet/))
      .toBeDefined();
    expect(screen.queryByRole("button", { name: /Publish/ })).toBeNull();
  });
});

describe("Getting the code", () => {
  it("names the commit the user owns", async () => {
    mockApi({});
    renderAt("/projects/p1/ship", <ShipPage />);

    expect(await screen.findByText("3a28a30d9de2aaaa")).toBeDefined();
  });

  it("says what is not built, one thing at a time", async () => {
    // "Coming soon" over three different things tells the user nothing about
    // which one they need. This screen used to be a placeholder apologising for
    // itself — on the one screen whose whole subject is ownership.
    mockApi({});
    renderAt("/projects/p1/ship", <ShipPage />);

    expect(await screen.findByText(/Downloading the repository/)).toBeDefined();
    expect(screen.getByText(/Pushing to your own remote/)).toBeDefined();
    expect(screen.getByText(/Publishing it somewhere permanent/)).toBeDefined();
  });

  it("sends you to build first when there is nothing to hand over", async () => {
    mockApi({ latestBuild: vi.fn().mockResolvedValue(latest({ buildVersion: null })) });
    renderAt("/projects/p1/ship", <ShipPage />);

    expect(await screen.findByText("Nothing has been built yet")).toBeDefined();
  });
});
