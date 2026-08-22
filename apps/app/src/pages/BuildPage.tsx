import type { BuildStarted } from "@scio/shared";
import { useEffect, useRef, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { Button, Eyebrow, Lede, PageTitle, StateCard } from "../components/ui";
import { lostConnection } from "../lib/api";
import { useApi } from "../lib/useApi";

/**
 * The build view. Every number on this screen comes from a part that has
 * actually finished — there is no timer and no fake bar, because a progress bar
 * that lies is the first thing that teaches a user not to trust the rest.
 *
 * The schedule is drawn from the engine's `started` event, so the user sees what
 * is coming before it happens rather than a list that grows out of nowhere.
 */

type PartState = "waiting" | "building" | "passed" | "needs_look" | "blocked" | "failed";

const PART_STYLES: Record<PartState, { mark: string; cls: string }> = {
  waiting: { mark: "○", cls: "text-muted" },
  building: { mark: "◍", cls: "text-teal" },
  passed: { mark: "✓", cls: "text-verified" },
  needs_look: { mark: "!", cls: "text-attention" },
  blocked: { mark: "—", cls: "text-muted" },
  failed: { mark: "×", cls: "text-danger" },
};

function readablePart(id: string): string {
  return id
    .replace(/^pkg_/, "")
    .replace(/^feature_/, "")
    .replace(/_/g, " ");
}

function Drafting() {
  return (
    <div className="h-[150px] bg-surface-2 border border-line rounded-card p-5 drafting overflow-hidden">
      <div className="h-3.5 w-[46%] bg-line-strong rounded-[3px] my-[9px]" />
      <div className="h-[9px] w-[80%] bg-line rounded-[3px] my-[9px]" />
      <div className="h-[9px] bg-line rounded-[3px] my-[9px]" />
      <div className="h-5 w-[32%] bg-teal opacity-50 rounded my-[9px]" />
    </div>
  );
}

export function BuildPage() {
  const { projectId = "" } = useParams();
  const api = useApi();
  const navigate = useNavigate();

  const [started, setStarted] = useState<BuildStarted | null>(null);
  const [states, setStates] = useState<Record<string, PartState>>({});
  const [lines, setLines] = useState<string[]>([]);
  const [done, setDone] = useState(0);
  const [error, setError] = useState<string | null>(null);
  /**
   * The connection died, which is NOT the same as the build dying.
   *
   * The lede one line up promises "you can leave this page — the build keeps
   * running", and then a dropped stream used to contradict it with "The build
   * stopped". It was wrong every time it appeared: the api had no failure to
   * report, the engine was still working, and the only thing that had ended was
   * this page's ability to hear about it.
   */
  const [disconnected, setDisconnected] = useState(false);
  const running = useRef(false);
  // Whether this component is still on screen. A ref, not a local, because
  // StrictMode unmounts and remounts: a local would be captured by the dead
  // first effect and never turned back on.
  const showing = useRef(true);

  useEffect(() => {
    showing.current = true;
    if (running.current) return; // StrictMode mounts twice; a build must not.
    running.current = true;

    // The stream is deliberately NOT aborted when this page goes away.
    //
    // It used to be, and in dev that killed every build instantly: StrictMode
    // mounts, unmounts and remounts, the cleanup aborted the one stream that
    // had started, the guard above stopped a second one, and the AbortError
    // surfaced as "Can't reach the Scio API — is the backend running?" on a
    // perfectly healthy backend. It also contradicted this screen's own promise
    // that you can leave and the build keeps running. So updates are gated on
    // whether anyone is looking, and the build is left to finish.
    api
      .streamBuild(
        projectId,
        (frame) => {
          if (!showing.current) return;
          // Switching on the name narrows the payload (B089): what used to be a
          // cast per branch is now the compiler's job.
          switch (frame.event) {
            case "started": {
              setStarted(frame.data);
              setStates(
                Object.fromEntries(frame.data.packages.map((id) => [id, "waiting"])),
              );
              break;
            }
            case "progress": {
              const { package_id, status, done: finishedParts, message } = frame.data;
              setStates((prev) => ({
                ...prev,
                [package_id]: status === "building" ? "building" : (status as PartState),
              }));
              if (status !== "building") {
                setDone(finishedParts);
                setLines((prev) => [...prev, message]);
              }
              break;
            }
            case "finished":
              navigate(`/projects/${projectId}/reveal`);
              break;
            case "error":
              setError(frame.data.message || "The build failed.");
              break;
          }
        },
      )
      .catch((err) => {
        if (!showing.current) return;
        if (lostConnection(err)) setDisconnected(true);
        else setError(err instanceof Error ? err.message : "The build failed.");
      });

    return () => {
      showing.current = false;
    };
  }, [api, projectId, navigate]);

  const total = started?.total ?? 0;
  const percent = total ? Math.round((done / total) * 100) : 0;

  return (
    <section>
      <Eyebrow>Building</Eyebrow>
      <PageTitle>Scio is building your app</PageTitle>
      <Lede>
        You can leave this page — the build keeps running and we'll let you know when it's ready.
      </Lede>

      {disconnected && !error && (
        <div className="mb-4">
          <StateCard
            icon="~"
            tone="warn"
            title="We lost the connection"
            action={
              <Button
                onClick={async () => {
                  // Re-read rather than re-subscribe: the build may well have
                  // finished while this page was deaf.
                  const latest = await api.latestBuild(projectId).catch(() => null);
                  if (latest?.buildVersion) navigate(`/projects/${projectId}/reveal`);
                  else window.location.reload();
                }}
              >
                Check on it
              </Button>
            }
          >
            The build keeps running on the server — this page just stopped hearing about it.
          </StateCard>
        </div>
      )}

      {error && (
        <div className="mb-4">
          <StateCard
            icon="!"
            tone="error"
            title="The build stopped"
            action={
              <Button variant="ghost" onClick={() => navigate(`/projects/${projectId}/spec`)}>
                Back to the spec
              </Button>
            }
          >
            {error}
          </StateCard>
        </div>
      )}

      <div className="grid grid-cols-[1fr_300px] max-md:grid-cols-1 gap-[18px]">
        <div className="bg-surface border border-line rounded-card p-[18px]">
          <Drafting />
          {started?.whole && (
            <p className="text-[13px] text-muted mt-4 leading-relaxed">{started.whole}</p>
          )}
          {started?.models && (
            // What is writing this code is not a detail: it is what the result
            // costs and how good it will be.
            <p className="font-mono text-[11px] text-muted mt-3" data-testid="build-models">
              {started.models}
            </p>
          )}
          <div className="font-mono text-[11px] text-muted mt-4" data-testid="build-log">
            {lines.slice(-6).map((line) => (
              <div key={line} className="py-0.5">
                {line}
              </div>
            ))}
          </div>
        </div>

        <aside className="bg-surface border border-line rounded-card p-[18px] relative self-start">
          <span className="absolute top-3 left-3 w-2.5 h-2.5 border-t-[1.5px] border-l-[1.5px] border-line-strong" />
          {/* A build runs for tens of minutes and changes on its own. Without a
              live region a screen-reader user has no way to know it moved —
              they would have to keep re-reading the page to find out. Polite,
              not assertive: it is progress, not an emergency. */}
          <div
            className="font-mono text-[11px] uppercase tracking-[0.14em] text-muted mb-3.5"
            role="status"
            aria-live="polite"
          >
            {total ? `${done} of ${total} parts done` : "Planning…"}
          </div>

          <div className="h-1 bg-surface-2 rounded-full mb-3.5 overflow-hidden">
            <i
              className="block h-full bg-teal rounded-full transition-[width] duration-500"
              style={{ width: `${percent}%` }}
            />
          </div>

          {(started?.packages ?? []).map((id) => {
            const state = states[id] ?? "waiting";
            const style = PART_STYLES[state];
            return (
              <div key={id} className="flex items-center gap-2 py-[5px] text-[13px]">
                <span className={`font-mono w-4 flex-none ${style.cls}`}>{style.mark}</span>
                <span className={state === "waiting" ? "text-muted" : ""}>{readablePart(id)}</span>
              </div>
            );
          })}

          {!started && !error && (
            <p className="text-[13px] text-muted">Working out what to build…</p>
          )}
        </aside>
      </div>
    </section>
  );
}
