import type { CorrectSpecFieldResponse, IntakeStepResponse } from "@scio/shared";
import { cleanup, render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";
import { ApiError } from "../lib/api";
import * as useApiModule from "../lib/useApi";
import { SpecPage } from "./SpecPage";

/**
 * B066: correcting a field the wizard filed wrongly.
 *
 * The defect being fixed is not "the value was wrong" — it is that the review
 * screen SHOWED it was wrong and offered no way out except starting over. So
 * what is tested here is the way out: one action moves an answer to the right
 * field, the whole screen re-renders from the corrected spec, and a correction
 * that opens new work says so and holds the approve button shut until it is
 * answered.
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

/** The actual misfiling: "guests and staff" filed under what the app manages. */
const MISFILED = {
  purpose: field("Guests book a table."),
  entities: field(["guests", "staff"]),
  key_actions: field(["book a table"]),
  sign_in: field("an email link"),
  data_ownership_sensitivity: field({ owner: "you", sensitive: false, kinds: [] }),
  look: field("Scio default", "default"),
};

const CORRECTED = {
  ...MISFILED,
  entities: undefined,
  users_and_roles: {
    value: ["guests", "staff"],
    source: "stated",
    confidence: "high",
    provenance: ["corrected-on-review"],
  },
};

function step(overrides: Partial<IntakeStepResponse> = {}): IntakeStepResponse {
  return {
    updated_spec: MISFILED,
    buildable: true,
    next_question: null,
    contradictions: [],
    gate: { buildable: true, missing_core: [], unresolved_conditionals: [], contradictions: [] },
    messages: [],
    whole: "You're building a table-booking app.",
    engine: { reachable: true },
    ...overrides,
  } as IntakeStepResponse;
}

function corrected(overrides: Partial<CorrectSpecFieldResponse> = {}): CorrectSpecFieldResponse {
  return {
    ...step({ updated_spec: CORRECTED as never }),
    newly_required: [],
    still_needed: [],
    changed: ["users_and_roles"],
    cleared: ["entities"],
    ...overrides,
  } as CorrectSpecFieldResponse;
}

function mockApi(overrides: Record<string, unknown> = {}) {
  const api = {
    getIntake: vi.fn().mockResolvedValue(step()),
    correctSpecField: vi.fn().mockResolvedValue(corrected()),
    approveSpec: vi.fn().mockResolvedValue({
      specVersion: { id: "s1", number: 1, isCurrent: true, createdAt: "2026-08-12T00:00:00Z" },
      projectStatus: "spec_locked",
    }),
    ...overrides,
  };
  vi.spyOn(useApiModule, "useApi").mockReturnValue(api as never);
  return api;
}

function renderSpec() {
  return render(
    <MemoryRouter initialEntries={["/projects/p1/spec"]}>
      <Routes>
        <Route path="/projects/:projectId/spec" element={<SpecPage />} />
      </Routes>
    </MemoryRouter>,
  );
}

async function openEditor(field: string) {
  const row = await screen.findByTestId(`row-${field}`);
  await userEvent.click(within(row).getByRole("button", { name: /correct/i }));
  return screen.getByTestId(`editor-${field}`);
}

describe("Correcting a field on the review screen", () => {
  it("every field offers a correction — that is the whole point of showing them", async () => {
    mockApi();
    renderSpec();

    const row = await screen.findByTestId("row-purpose");
    expect(within(row).getByRole("button", { name: /correct/i })).toBeDefined();
  });

  it("changing a value sends the field and the new value", async () => {
    const api = mockApi();
    renderSpec();

    const editor = await openEditor("purpose");
    const input = within(editor).getByLabelText("What it does");
    await userEvent.clear(input);
    await userEvent.type(input, "Staff manage tonight's tables.");
    await userEvent.click(within(editor).getByRole("button", { name: "Save" }));

    await waitFor(() =>
      expect(api.correctSpecField).toHaveBeenCalledWith("p1", {
        field: "purpose",
        value: "Staff manage tonight's tables.",
      }),
    );
  });

  it("a list is typed as a list and split here, not on the server", async () => {
    const api = mockApi();
    renderSpec();

    const editor = await openEditor("entities");
    const input = within(editor).getByLabelText("What it manages");
    await userEvent.clear(input);
    await userEvent.type(input, "bookings, tables, guests");
    await userEvent.click(within(editor).getByRole("button", { name: "Save" }));

    await waitFor(() =>
      expect(api.correctSpecField).toHaveBeenCalledWith("p1", {
        field: "entities",
        value: ["bookings", "tables", "guests"],
      }),
    );
  });

  it("moving an answer to the right field sets it there AND empties the wrong one", async () => {
    // The defect itself: one action, one request — the spec is never left
    // holding the same answer under two headings.
    const api = mockApi();
    renderSpec();

    const editor = await openEditor("entities");
    await userEvent.selectOptions(within(editor).getByLabelText("Belongs under"), "users_and_roles");
    await userEvent.click(within(editor).getByRole("button", { name: /move it there/i }));

    await waitFor(() =>
      expect(api.correctSpecField).toHaveBeenCalledWith("p1", {
        field: "users_and_roles",
        value: ["guests", "staff"],
        clear: ["entities"],
      }),
    );
  });

  it("the whole screen re-renders from the corrected spec", async () => {
    // Not just the edited row: the narrative and the assumptions are derived
    // from the spec, and prose describing a spec that no longer exists is
    // exactly what this screen exists to prevent.
    mockApi({
      correctSpecField: vi.fn().mockResolvedValue(
        corrected({ whole: "You're building a table-booking app for guests and staff." }),
      ),
    });
    renderSpec();

    const editor = await openEditor("entities");
    await userEvent.selectOptions(within(editor).getByLabelText("Belongs under"), "users_and_roles");
    await userEvent.click(within(editor).getByRole("button", { name: /move it there/i }));

    expect(await screen.findByText(/for guests and staff/)).toBeDefined();
    expect(await screen.findByTestId("row-users_and_roles")).toBeDefined();
    expect(screen.queryByTestId("row-entities")).toBeNull();
  });

  it("the sensitivity field gets its three parts, not a JSON blob", async () => {
    const api = mockApi();
    renderSpec();

    const editor = await openEditor("data_ownership_sensitivity");
    await userEvent.click(within(editor).getByLabelText("Some of it is sensitive"));
    await userEvent.type(within(editor).getByLabelText("What kind"), "personal");
    await userEvent.click(within(editor).getByRole("button", { name: "Save" }));

    await waitFor(() =>
      expect(api.correctSpecField).toHaveBeenCalledWith("p1", {
        field: "data_ownership_sensitivity",
        value: { owner: "you", sensitive: true, kinds: ["personal"] },
      }),
    );
  });

  it("a refusal is shown and the screen keeps the spec it had", async () => {
    mockApi({
      correctSpecField: vi.fn().mockRejectedValue(new ApiError(400, "'purpose' needs a sentence")),
    });
    renderSpec();

    const editor = await openEditor("purpose");
    await userEvent.click(within(editor).getByRole("button", { name: "Save" }));

    expect(await screen.findByText(/needs a sentence/)).toBeDefined();
    expect(screen.getByTestId("editor-purpose")).toBeDefined();
  });
});

describe("A correction that opens new work", () => {
  const opened = corrected({
    buildable: false,
    gate: {
      buildable: false,
      missing_core: [],
      unresolved_conditionals: ["role_permissions"],
      contradictions: [],
    },
    newly_required: ["role_permissions"],
    still_needed: ["role_permissions"],
    whole: null,
  });

  it("says what it opened and asks for it inline", async () => {
    mockApi({ correctSpecField: vi.fn().mockResolvedValue(opened) });
    renderSpec();

    const editor = await openEditor("entities");
    await userEvent.selectOptions(within(editor).getByLabelText("Belongs under"), "users_and_roles");
    await userEvent.click(within(editor).getByRole("button", { name: /move it there/i }));

    const panel = await screen.findByTestId("still-needed");
    expect(within(panel).getByText(/That change needs a bit more/)).toBeDefined();
    // Answerable right here — the entire point is not going back to the wizard.
    expect(within(panel).getByTestId("editor-role_permissions")).toBeDefined();
    expect(within(panel).getByText(/don't have to go back to the wizard/)).toBeDefined();
  });

  it("holds the gate shut until it is answered", async () => {
    mockApi({ correctSpecField: vi.fn().mockResolvedValue(opened) });
    renderSpec();

    const editor = await openEditor("entities");
    await userEvent.selectOptions(within(editor).getByLabelText("Belongs under"), "users_and_roles");
    await userEvent.click(within(editor).getByRole("button", { name: /move it there/i }));

    await screen.findByTestId("still-needed");
    const approve = screen.getByRole("button", { name: /yes, build it/i });
    expect((approve as HTMLButtonElement).disabled).toBe(true);
  });

  it("answering it inline opens the gate again", async () => {
    const correctSpecField = vi
      .fn()
      .mockResolvedValueOnce(opened)
      .mockResolvedValueOnce(corrected({ changed: ["role_permissions"] }));
    mockApi({ correctSpecField });
    renderSpec();

    const editor = await openEditor("entities");
    await userEvent.selectOptions(within(editor).getByLabelText("Belongs under"), "users_and_roles");
    await userEvent.click(within(editor).getByRole("button", { name: /move it there/i }));

    const panel = await screen.findByTestId("still-needed");
    const inline = within(panel).getByTestId("editor-role_permissions");
    await userEvent.type(
      within(inline).getByLabelText("Who may do what"),
      "Staff see today's list.",
    );
    await userEvent.click(within(inline).getByRole("button", { name: "Save" }));

    await waitFor(() => expect(screen.queryByTestId("still-needed")).toBeNull());
    const approve = screen.getByRole("button", { name: /yes, build it/i });
    expect((approve as HTMLButtonElement).disabled).toBe(false);
  });

  it("a field asked for inline offers no 'belongs under' — it IS the field being asked", async () => {
    mockApi({ correctSpecField: vi.fn().mockResolvedValue(opened) });
    renderSpec();

    const editor = await openEditor("entities");
    await userEvent.selectOptions(within(editor).getByLabelText("Belongs under"), "users_and_roles");
    await userEvent.click(within(editor).getByRole("button", { name: /move it there/i }));

    const inline = within(await screen.findByTestId("still-needed")).getByTestId(
      "editor-role_permissions",
    );
    expect(within(inline).queryByLabelText("Belongs under")).toBeNull();
  });

  it("a contradiction is shown with the fields to correct", async () => {
    mockApi({
      getIntake: vi.fn().mockResolvedValue(
        step({
          buildable: false,
          gate: {
            buildable: false,
            missing_core: [],
            unresolved_conditionals: [],
            contradictions: [],
          },
          contradictions: [
            {
              fields: ["sign_in", "role_permissions"],
              description: "nobody signs in, but people should see their own data",
              resolved: false,
            },
          ],
        }),
      ),
    });
    renderSpec();

    const panel = await screen.findByTestId("still-needed");
    expect(within(panel).getByText(/but people should see their own data/)).toBeDefined();
    expect(within(panel).getByText(/Sign-in or Who may do what/)).toBeDefined();
  });
});
