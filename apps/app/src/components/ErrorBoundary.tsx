import { Component, type ErrorInfo, type ReactNode } from "react";
import { Button } from "./ui";

/**
 * One thrown render must not blank the page.
 *
 * React unmounts the whole tree when a render throws, so without this the user
 * gets a white screen with no message and no way back — after a build they paid
 * for. What is shown says what happened and offers the two things that actually
 * help: reload, or go back to the projects list. Nothing here pretends the
 * error did not happen.
 */
interface State {
  error: Error | null;
}

export class ErrorBoundary extends Component<{ children: ReactNode }, State> {
  state: State = { error: null };

  static getDerivedStateFromError(error: Error): State {
    return { error };
  }

  componentDidCatch(error: Error, info: ErrorInfo): void {
    // The console is the only reporter there is today. When error reporting
    // arrives (B098), this is where it hooks in.
    console.error("Scio crashed while rendering", error, info.componentStack);
  }

  render(): ReactNode {
    const { error } = this.state;
    if (!error) return this.props.children;
    return (
      <div className="flex min-h-[60vh] flex-col items-center justify-center gap-3.5 text-center">
        <div className="flex h-11 w-11 items-center justify-center rounded-btn bg-danger text-xl text-on-teal">
          !
        </div>
        <h1 className="font-display text-[28px] font-semibold tracking-tight">
          Something in Scio broke
        </h1>
        <p className="max-w-md text-sm text-muted">
          Not your app — this screen. Your work is saved; nothing you built is affected.
        </p>
        <p className="max-w-md font-mono text-xs text-muted">{error.message}</p>
        <div className="flex gap-2">
          <Button onClick={() => window.location.reload()}>Reload</Button>
          <Button variant="ghost" onClick={() => (window.location.href = "/projects")}>
            Back to projects
          </Button>
        </div>
      </div>
    );
  }
}
