import type { IntakeStepResponse } from "@scio/shared";
import { cleanup, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";
import * as useApiModule from "../lib/useApi";
import { SpecPage } from "./SpecPage";
import { WizardPage } from "./WizardPage";

/**
 * Gate 1's wiring, with the API mocked. What matters here is that the screens
 * read the *real* response shape — spec metadata included — because the "assumed"
 * tags and the buildable transition are the product promises this screen makes.
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

function field(value: unknown, source = "stated") {
  return { value, source, confidence: "high", provenance: ["m1"] };
}

const SPEC = {
  purpose: field("Guests book a table and get a confirmation."),
  users_and_roles: field(["guests"]),
  entities: field(["bookings", "tables"], "derived"),
  platform: field("responsive web app", "default"),
  look: field("Scio default", "default"),
};

function step(overrides: Partial<IntakeStepResponse> = {}): IntakeStepResponse {
  return {
    updated_spec: SPEC,
    buildable: false,
    next_question: null,
    contradictions: [],
    gate: { buildable: false, missing_core: [], unresolved_conditionals: [], contradictions: [] },
    messages: [],
    engine: { reachable: true },
    ...overrides,
  } as IntakeStepResponse;
}

function mockApi(overrides: Record<string, unknown>) {
  const api = {
    getIntake: vi.fn().mockResolvedValue(step()),
    sendIntakeMessage: vi.fn().mockResolvedValue(step()),
    approveSpec: vi.fn().mockResolvedValue({
      specVersion: { id: "s1", number: 1, isCurrent: true, createdAt: "2026-08-12T00:00:00Z" },
      projectStatus: "spec_locked",
    }),
    ...overrides,
  };
  vi.spyOn(useApiModule, "useApi").mockReturnValue(api as never);
  return api;
}

function renderAt(path: string, element: JSX.Element) {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <Routes>
        <Route path="/projects/:projectId/wizard" element={element} />
        <Route path="/projects/:projectId/spec" element={element} />
      </Routes>
    </MemoryRouter>,
  );
}

describe("Wizard", () => {
  it("shows an opening question and an empty panel before anything has been said", async () => {
    mockApi({ getIntake: vi.fn().mockResolvedValue(step({ updated_spec: {} })) });
    renderAt("/projects/p1/wizard", <WizardPage />);

    expect(await screen.findByText(/What should the app do\?/)).toBeDefined();
    expect(screen.getByText(/Nothing yet/)).toBeDefined();
    expect(screen.getByText(/0 of 6 core answers/)).toBeDefined();
  });

  it("sends a turn and renders the next question with its example", async () => {
    const api = mockApi({
      sendIntakeMessage: vi.fn().mockResolvedValue(
        step({
          messages: [
            { id: "m1", role: "user", text: "A booking app for my restaurant." },
            {
              id: "m2",
              role: "scio",
              text: "Who will be using it? For example: Guests, and staff.",
              example: "Guests, and staff.",
            },
          ],
          next_question: {
            field: "users_and_roles",
            text: "Who will be using it?",
            example: "Guests, and staff.",
            about: "field",
            written_by: "model",
          },
        }),
      ),
    });
    renderAt("/projects/p1/wizard", <WizardPage />);

    await userEvent.type(
      await screen.findByLabelText("Your answer"),
      "A booking app for my restaurant.",
    );
    await userEvent.click(screen.getByRole("button", { name: /Send/ }));

    expect(api.sendIntakeMessage).toHaveBeenCalledWith("p1", "A booking app for my restaurant.");
    expect(await screen.findByText("Who will be using it?")).toBeDefined();
    expect(screen.getByText(/Ex: “Guests, and staff.”/)).toBeDefined();
  });

  it("fills the wholeness panel from the spec, tagging assumptions", async () => {
    mockApi({});
    renderAt("/projects/p1/wizard", <WizardPage />);

    expect(await screen.findByText("What it does")).toBeDefined();
    expect(screen.getByText(/Guests book a table and get a confirmation./)).toBeDefined();
    // Assumed and inferred are visibly different from what the user stated.
    expect(screen.getAllByText("assumed")).toHaveLength(2); // platform, look
    expect(screen.getAllByText("inferred")).toHaveLength(1); // entities (derived)
    expect(screen.getByText(/3 of 6 core answers/)).toBeDefined();
  });

  it("surfaces a contradiction as something the user must decide", async () => {
    mockApi({
      getIntake: vi.fn().mockResolvedValue(
        step({
          contradictions: [
            {
              fields: ["sign_in", "users_and_roles"],
              description: "You said no sign-in, but also that staff need their own view.",
              resolved: false,
            },
          ],
        }),
      ),
    });
    renderAt("/projects/p1/wizard", <WizardPage />);

    expect(await screen.findByText(/Needs your call/)).toBeDefined();
    expect(screen.getByText(/no sign-in, but also that staff/)).toBeDefined();
  });

  it("moves to the review screen when the spec becomes buildable", async () => {
    mockApi({ sendIntakeMessage: vi.fn().mockResolvedValue(step({ buildable: true })) });
    renderAt("/projects/p1/wizard", <WizardPage />);

    await userEvent.type(await screen.findByLabelText("Your answer"), "that's everything");
    await userEvent.click(screen.getByRole("button", { name: /Send/ }));

    await waitFor(() => expect(navigate).toHaveBeenCalledWith("/projects/p1/spec"));
  });

  it("keeps the continue button shut until the gate opens", async () => {
    mockApi({});
    renderAt("/projects/p1/wizard", <WizardPage />);

    const button = await screen.findByRole("button", { name: /Continue to review/ });
    expect((button as HTMLButtonElement).disabled).toBe(true);
  });

  it("shows a failed turn without losing the conversation", async () => {
    const { ApiError } = await import("../lib/api");
    mockApi({
      sendIntakeMessage: vi.fn().mockRejectedValue(new ApiError(503, "The Scio engine is not reachable.")),
    });
    renderAt("/projects/p1/wizard", <WizardPage />);

    await userEvent.type(await screen.findByLabelText("Your answer"), "hello?");
    await userEvent.click(screen.getByRole("button", { name: /Send/ }));

    expect(await screen.findByText(/engine is not reachable/)).toBeDefined();
    expect(screen.getByText("What it does")).toBeDefined(); // the panel survived
  });
});

describe("Review (spec gate)", () => {
  it("shows the whole above the spec — never instead of it", async () => {
    mockApi({
      getIntake: vi.fn().mockResolvedValue(
        step({ buildable: true, whole: "You're building a table-booking app for your guests." }),
      ),
    });
    renderAt("/projects/p1/spec", <SpecPage />);

    expect(await screen.findByText(/You're building a table-booking app/)).toBeDefined();
    // The spec is what gets frozen, so it stays visible under the prose.
    expect(screen.getByText("What it does")).toBeDefined();
    expect(screen.getByText("In detail:")).toBeDefined();
  });

  it("falls back to the structured spec when the whole is unavailable", async () => {
    mockApi({
      getIntake: vi
        .fn()
        .mockResolvedValue(
          step({ buildable: true, whole: null, engine: { reachable: true, degraded: ["architecture"] } }),
        ),
    });
    renderAt("/projects/p1/spec", <SpecPage />);

    expect(await screen.findByText(/field by field/)).toBeDefined();
    expect(screen.getByText("What it does")).toBeDefined();
    expect(screen.getByText(/written summary wasn't available/)).toBeDefined();
  });

  it("lists the assumptions it made", async () => {
    mockApi({ getIntake: vi.fn().mockResolvedValue(step({ buildable: true })) });
    renderAt("/projects/p1/spec", <SpecPage />);

    expect(await screen.findByText(/Assumptions I made/)).toBeDefined();
    expect(screen.getByText(/Platform: responsive web app/)).toBeDefined();
    expect(screen.getByText(/Look: Scio default/)).toBeDefined();
  });

  it("marks the part count as rough, never as a price", async () => {
    mockApi({
      getIntake: vi.fn().mockResolvedValue(
        step({
          buildable: true,
          estimate: { parts: 5, rough: true, packages: ["pkg_foundation"] },
        }),
      ),
    });
    renderAt("/projects/p1/spec", <SpecPage />);

    const line = await screen.findByText(/Roughly 5 parts to build/);
    expect(line.textContent).toContain("not a price");
  });

  it("freezes the spec and lands on the locked state", async () => {
    const api = mockApi({ getIntake: vi.fn().mockResolvedValue(step({ buildable: true })) });
    renderAt("/projects/p1/spec", <SpecPage />);

    await userEvent.click(await screen.findByRole("button", { name: /Yes, build it/ }));

    expect(api.approveSpec).toHaveBeenCalledWith("p1");
    expect(await screen.findByText("Spec locked")).toBeDefined();
    expect(screen.getByText(/Version 1 is frozen/)).toBeDefined();
    expect(screen.getByText(/Build is next/)).toBeDefined();
  });

  it("offers the two other exits", async () => {
    mockApi({ getIntake: vi.fn().mockResolvedValue(step({ buildable: true })) });
    renderAt("/projects/p1/spec", <SpecPage />);

    await userEvent.click(await screen.findByRole("button", { name: /let me adjust/ }));
    expect(navigate).toHaveBeenCalledWith("/projects/p1/wizard");

    await userEvent.click(screen.getByRole("button", { name: /Not now/ }));
    expect(navigate).toHaveBeenCalledWith("/projects");
  });
});
