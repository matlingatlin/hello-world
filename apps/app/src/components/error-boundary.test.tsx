import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { ErrorBoundary } from "./ErrorBoundary";

function Explodes(): never {
  throw new Error("the reveal could not render");
}

describe("when a render throws", () => {
  it("says what happened instead of blanking the page", () => {
    // React logs the error itself; silence it so the suite output stays honest.
    const quiet = vi.spyOn(console, "error").mockImplementation(() => {});

    render(
      <ErrorBoundary>
        <Explodes />
      </ErrorBoundary>,
    );

    expect(screen.getByText(/Something in Scio broke/i)).toBeTruthy();
    expect(screen.getByText(/the reveal could not render/)).toBeTruthy();
    // and it says the thing the user actually needs to hear
    expect(screen.getByText(/nothing you built is affected/i)).toBeTruthy();
    quiet.mockRestore();
  });

  it("renders its children when nothing throws", () => {
    render(
      <ErrorBoundary>
        <p>the app</p>
      </ErrorBoundary>,
    );
    expect(screen.getByText("the app")).toBeTruthy();
  });
});

describe("what changes without the user acting", () => {
  /**
   * A build runs for tens of minutes and moves on its own; an error card
   * appears because something happened, not because anyone clicked. Neither was
   * announced, so a screen-reader user had to keep re-reading the page to find
   * out whether anything had changed.
   */
  it("announces an error card as an alert", async () => {
    const { StateCard } = await import("./ui");
    // Scoped to this render: the queries off `screen` search the whole document,
    // and without cleanup a card from an earlier test is still in it.
    const view = render(
      <StateCard icon="!" tone="error" title="The build stopped">
        network error
      </StateCard>,
    );
    expect(view.getByRole("alert")).toBeTruthy();
    view.unmount();
  });

  it("announces a non-error card politely, not as an alert", async () => {
    const { StateCard } = await import("./ui");
    const view = render(
      <StateCard icon="i" title="Nothing here yet">
        make a project
      </StateCard>,
    );
    expect(view.getByRole("status")).toBeTruthy();
    expect(view.queryByRole("alert")).toBeNull();
    view.unmount();
  });
});
