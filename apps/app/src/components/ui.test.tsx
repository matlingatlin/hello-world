import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { Button, StatusChip, StateCard } from "./ui";

describe("ui components", () => {
  afterEach(cleanup);

  it("renders status chips with the prototype's labels", () => {
    render(
      <>
        <StatusChip status="ready" />
        <StatusChip status="building" />
        <StatusChip status="draft" />
        <StatusChip status="error" />
      </>,
    );
    expect(screen.getByText("Works")).toBeTruthy();
    expect(screen.getByText("Building…")).toBeTruthy();
    expect(screen.getByText("Draft")).toBeTruthy();
    expect(screen.getByText("Error")).toBeTruthy();
  });

  it("renders primary and ghost buttons", () => {
    render(
      <>
        <Button>Create</Button>
        <Button variant="ghost">Retry</Button>
      </>,
    );
    expect(screen.getByText("Create").className).toContain("bg-teal");
    expect(screen.getByText("Retry").className).toContain("bg-transparent");
  });

  it("renders state cards with title, body, and action", () => {
    render(
      <StateCard icon="!" tone="error" title="Couldn't load" action={<Button>Retry</Button>}>
        The API is unreachable.
      </StateCard>,
    );
    expect(screen.getByText("Couldn't load")).toBeTruthy();
    expect(screen.getByText("The API is unreachable.")).toBeTruthy();
    expect(screen.getByText("Retry")).toBeTruthy();
  });
});
