import type { Project } from "@scio/shared";
import { cleanup, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";
import * as useApiModule from "../lib/useApi";
import { ProjectsPage } from "./ProjectsPage";

/**
 * The projects list is the way back in.
 *
 * It had none: the cards were styled `cursor-pointer`, hovered like a link, and
 * had no click handler at all — so a person who left a project could not return
 * to it, and the only route back was the browser's history. Found by clicking
 * the real app, not by a test, which is why there is one now.
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

function project(overrides: Partial<Project> = {}): Project {
  return {
    id: "p1",
    workspaceId: "w1",
    name: "Bistro Nord",
    type: "app",
    status: "draft",
    deletedAt: null,
    createdAt: "2026-08-20T00:00:00Z",
    updatedAt: "2026-08-22T00:00:00Z",
    ...overrides,
  };
}

function mockApi(projects: Project[]) {
  const api = { listProjects: vi.fn().mockResolvedValue({ projects }) };
  vi.spyOn(useApiModule, "useApi").mockReturnValue(api as never);
  return api;
}

function renderList() {
  return render(
    <MemoryRouter initialEntries={["/projects"]}>
      <Routes>
        <Route path="/projects" element={<ProjectsPage />} />
      </Routes>
    </MemoryRouter>,
  );
}

describe("Opening a project", () => {
  it("puts a draft back in the wizard", async () => {
    mockApi([project({ status: "draft" })]);
    renderList();

    await userEvent.click(await screen.findByRole("button", { name: "Open Bistro Nord" }));

    expect(navigate).toHaveBeenCalledWith("/projects/p1/wizard");
  });

  it("puts an approved spec at the involvement question", async () => {
    mockApi([project({ status: "spec_locked" })]);
    renderList();

    await userEvent.click(await screen.findByRole("button", { name: "Open Bistro Nord" }));

    expect(navigate).toHaveBeenCalledWith("/projects/p1/involve");
  });

  it("puts a running build back on the build screen", async () => {
    mockApi([project({ status: "building" })]);
    renderList();

    await userEvent.click(await screen.findByRole("button", { name: "Open Bistro Nord" }));

    expect(navigate).toHaveBeenCalledWith("/projects/p1/build");
  });

  it("puts a finished app at the reveal", async () => {
    // Not the wizard: a finished app asking its owner to describe it again is
    // the worst answer available.
    mockApi([project({ status: "ready" })]);
    renderList();

    await userEvent.click(await screen.findByRole("button", { name: "Open Bistro Nord" }));

    expect(navigate).toHaveBeenCalledWith("/projects/p1/reveal");
  });

  it("is reachable from a keyboard", async () => {
    // It was a <div>. Decoration that only a mouse can use is not a control.
    mockApi([project()]);
    renderList();

    const card = await screen.findByRole("button", { name: "Open Bistro Nord" });
    card.focus();
    await userEvent.keyboard("{Enter}");

    expect(navigate).toHaveBeenCalledWith("/projects/p1/wizard");
  });
});
