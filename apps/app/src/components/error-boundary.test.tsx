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
