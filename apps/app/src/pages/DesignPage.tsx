import type {
  ApplyDesignChangeResponse,
  DesignConflict,
  DesignVersion,
  DesignVersionRef,
} from "@scio/shared";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { Button, Eyebrow, Lede, PageTitle, StateCard } from "../components/ui";
import { ApiError, lostConnection } from "../lib/api";
import { connectBridge, originOf, type Bridge, type BridgeHit } from "../lib/bridge";
import { useApi } from "../lib/useApi";

/**
 * Level 2 — the design window. "Show me before you build it."
 *
 * The shape of this screen is one decision: **the pending list IS the change
 * set.** You mark things, each becomes a line with a note you can edit or
 * remove, and "Generate again" applies all of them at once. There is no
 * separate select-then-apply step, because a change is usually several small
 * things noticed together, and making people submit them one at a time is what
 * makes a design tool feel expensive to use.
 *
 * The second decision: **conflicts are answered here.** A marking that argues
 * with the approved spec comes back as a question and nothing is built. You can
 * drop the marking, or change the plan — and changing the plan is a real,
 * recorded spec amendment, not a checkbox. Sending someone back to the wizard to
 * say "actually anyone should see the menu" would be bad product; letting them
 * quietly delete sign-in from a side panel would be worse.
 *
 * Nothing here resolves a marking. The preview reports, the engine decides, and
 * the manifest below is used only to *name* the package next to a line so the
 * user can see the change is aimed where they think it is.
 */

interface Pending {
  key: string;
  hit: BridgeHit;
  route: string;
  note: string;
}

/**
 * The preview's life, as four states rather than six flags.
 *
 * `disconnected` is its own state and not a kind of failure: a preview is a
 * real build on the server and it carries on without this page. Reported as a
 * failure it sent the user back to rebuild something that was already being
 * built; reported as nothing at all — which is what a stream that simply ends
 * looks like — it left the screen on "Working out what to build…" forever.
 */
type Preview =
  | { kind: "preparing"; lines: string[] }
  | { kind: "disconnected" }
  | { kind: "failed"; message: string }
  | { kind: "ready"; url: string; manifest: Record<string, unknown> | null };

/** The manifest as the engine writes it — enough of it to name a package. */
interface ManifestShape {
  elements?: Record<string, { package?: string; file?: string; line?: number }>;
}

function locate(
  manifest: Record<string, unknown> | null,
  scioId: string | null,
): { package: string; where: string } | null {
  if (!scioId || !manifest) return null;
  const entry = (manifest as ManifestShape).elements?.[scioId];
  if (!entry) return null;
  return {
    package: entry.package ?? "",
    where: entry.file ? `${entry.file}:${entry.line ?? 0}` : "",
  };
}

function readableId(id: string): string {
  return id.replace(/^pkg_/, "").replace(/_/g, " ");
}

function parseRef(version: DesignVersion | null | undefined): DesignVersionRef {
  if (!version?.ref) return {};
  try {
    return JSON.parse(version.ref) as DesignVersionRef;
  } catch {
    return {};
  }
}

/** A security conflict is confirmed twice; a scope conflict once. */
function isSecurity(conflict: DesignConflict): boolean {
  return conflict.kind === "auth" || conflict.kind === "access";
}

export function DesignPage() {
  const { projectId = "" } = useParams();
  const api = useApi();
  const navigate = useNavigate();

  /**
   * Where the preview is in its life. One value, four states (B090).
   *
   * This was six `useState`s — `previewUrl`, `manifest`, `preparing`, `lines`,
   * `error`, `disconnected` — which is 2^6 combinations for four real ones, and
   * the impossible ones were reachable: preparing with a url, an error with a
   * url, disconnected while preparing. The render had to spell out which
   * combinations it believed in (`preparing || (!previewUrl && !error)`), and
   * every new branch had to guess again.
   */
  const [preview, setPreview] = useState<Preview>({ kind: "preparing", lines: [] });
  const [whole, setWhole] = useState<string | null>(null);
  const [versions, setVersions] = useState<DesignVersion[]>([]);
  /**
   * Something the user asked for did not work, while the preview is fine.
   *
   * Kept apart from the preview's own failure on purpose: "the preview could
   * not be built" ends the screen, and "that version could not be restored" is
   * a line above a screen that still works. They were the same `error` before,
   * which is why the render had to reason about which one it was holding.
   */
  const [notice, setNotice] = useState<string | null>(null);

  const [mode, setMode] = useState<"use" | "mark">("use");
  const [pending, setPending] = useState<Pending[]>([]);
  const [prompt, setPrompt] = useState("");
  const [applying, setApplying] = useState(false);
  const [outcome, setOutcome] = useState<ApplyDesignChangeResponse | null>(null);
  const [conflicts, setConflicts] = useState<DesignConflict[]>([]);
  const [confirming, setConfirming] = useState<DesignConflict | null>(null);
  const [restoring, setRestoring] = useState<string | null>(null);

  /**
   * Every page the app has, and which one the frame is showing.
   *
   * The window used to embed the app's front door and offer no way to reach
   * anything else, so on a booking app you could mark up the home page and
   * nothing else — the parts most likely to need changing were the ones you
   * could not point at (B069). The list comes from the plan that built the app,
   * so it is what exists rather than what was hoped for.
   */
  const [routes, setRoutes] = useState<string[]>([]);
  const [route, setRoute] = useState("/");

  const [reachable, setReachable] = useState<boolean | null>(null);
  const [loaded, setLoaded] = useState(false);
  const [nudge, setNudge] = useState(0); // cache-buster for the iframe

  const frameRef = useRef<HTMLIFrameElement | null>(null);
  const bridgeRef = useRef<Bridge | null>(null);
  const startedRef = useRef(false);
  const modeRef = useRef<"use" | "mark">("use");
  // Whether anyone is still looking. A ref, not a local: StrictMode unmounts and
  // remounts, and a local would be captured by the dead first effect.
  const showing = useRef(true);

  const refreshVersions = useCallback(() => {
    api
      .listDesignVersions(projectId)
      .then((res) => showing.current && setVersions(res.designVersions))
      .catch(() => undefined);
  }, [api, projectId]);

  /**
   * Build the preview, streamed.
   *
   * Deliberately NOT aborted on unmount: the preview is a real build, and
   * aborting it on a StrictMode remount killed every build in dev (B064).
   */
  const rebuild = useCallback(async () => {
    setPreview({ kind: "preparing", lines: [] });
    setNotice(null);
    setReachable(null);
    try {
      await api.streamDesignPreview(projectId, (frame) => {
        if (!showing.current) return;
        // The payload follows from the name (B089) — no casts, and no reading a
        // field off an event that never carries it.
        switch (frame.event) {
          case "progress":
            if (frame.data.status !== "building") {
              const line = frame.data.message;
              setPreview((prev) =>
                prev.kind === "preparing" ? { ...prev, lines: [...prev.lines, line] } : prev,
              );
            }
            break;
          case "finished":
            setPreview({
              kind: "ready",
              url: frame.data.app_url || "",
              manifest: frame.data.manifest ?? null,
            });
            setRoutes(frame.data.routes ?? []);
            setWhole(frame.data.whole || null);
            setNudge((n) => n + 1);
            break;
          case "error":
            setPreview({
              kind: "failed",
              message: frame.data.message || "The preview could not be built.",
            });
            break;
        }
      });
    } catch (err) {
      if (!showing.current) return;
      setPreview(
        lostConnection(err)
          ? { kind: "disconnected" }
          : {
              kind: "failed",
              message: err instanceof ApiError ? err.message : "The preview could not be built.",
            },
      );
    } finally {
      refreshVersions();
    }
  }, [api, projectId, refreshVersions]);

  /**
   * Re-read rather than re-subscribe: the preview may well have finished while
   * this page was deaf, and asking for another build would throw away the one
   * that is already running.
   */
  const checkOnPreview = useCallback(async () => {
    setPreview({ kind: "preparing", lines: [] });
    const current = await api.getDesign(projectId).catch(() => null);
    if (!showing.current) return;
    if (current?.previewUrl) {
      setPreview({ kind: "ready", url: current.previewUrl, manifest: current.manifest });
      setRoutes(current.routes ?? []);
      setWhole(current.whole);
      refreshVersions();
      return;
    }
    await rebuild();
  }, [api, projectId, refreshVersions, rebuild]);

  // --- getting a preview -------------------------------------------------
  useEffect(() => {
    showing.current = true;
    if (startedRef.current) return; // StrictMode mounts twice; a build must not.
    startedRef.current = true;

    api
      .getDesign(projectId)
      .then((current) => {
        if (!showing.current) return;
        setWhole(current.whole);
        if (current.previewUrl) {
          setPreview({ kind: "ready", url: current.previewUrl, manifest: current.manifest });
          setRoutes(current.routes ?? []);
          refreshVersions();
          return;
        }
        return rebuild();
      })
      .catch((err) => {
        if (!showing.current) return;
        setPreview(
          lostConnection(err)
            ? { kind: "disconnected" }
            : {
                kind: "failed",
                message:
                  err instanceof ApiError ? err.message : "The preview could not be built.",
              },
        );
      });

    return () => {
      showing.current = false;
    };
  }, [api, projectId, refreshVersions, rebuild]);

  // Read straight off the state machine. Derived, not stored: a second copy of
  // the url is a second thing that can disagree with the first.
  const previewUrl = preview.kind === "ready" ? preview.url : null;
  const manifest = preview.kind === "ready" ? preview.manifest : null;

  // --- the bridge --------------------------------------------------------
  useEffect(() => {
    if (!previewUrl) return;
    const bridge = connectBridge(() => frameRef.current?.contentWindow ?? null, previewUrl, {
      onReady: () => {
        setReachable(true);
        // From the ref, not from `mode`: this fires again every time the iframe
        // reloads, and a captured `mode` would be whatever it was when the
        // preview first appeared — so marking would go quiet after a change.
        bridge.arm(modeRef.current === "mark");
      },
      onMarked: (marked) => {
        setPending((prev) => [
          ...prev,
          {
            key: `${marked.hit.scio_id ?? "unaddressable"}-${prev.length}-${Date.now()}`,
            hit: marked.hit,
            route: marked.route,
            note: "",
          },
        ]);
      },
    });
    bridgeRef.current = bridge;
    return () => {
      bridge.stop();
      bridgeRef.current = null;
    };
    // Keyed on the preview alone: re-connecting the listener on every toggle
    // would drop messages mid-click.
  }, [previewUrl]);

  useEffect(() => {
    modeRef.current = mode;
    bridgeRef.current?.arm(mode === "mark");
  }, [mode]);

  /**
   * If the bridge never says hello, marking will silently do nothing — so say so.
   *
   * The usual cause is an origin mismatch: the bridge posts only to the origin
   * the api was configured with (APP_ORIGIN), so opening this page on
   * `localhost` when that says `127.0.0.1` looks exactly like a broken preview.
   *
   * The countdown starts at the iframe's `load`, NOT when the page renders. A
   * dev preview compiles on first request and can take half a minute; timing
   * from render made the warning appear on a preview that was merely still
   * starting, which is the same crying-wolf that teaches people to ignore it.
   */
  useEffect(() => {
    if (!previewUrl || !loaded) return;
    const timer = setTimeout(() => setReachable((known) => known ?? false), 5000);
    return () => clearTimeout(timer);
  }, [previewUrl, loaded]);

  useEffect(() => {
    setReachable(null);
    setLoaded(false);
  }, [previewUrl, route, nudge]);

  const frameSrc = useMemo(() => {
    if (!previewUrl) return "";
    // The route is part of the src rather than something the iframe is asked to
    // navigate to: we cannot script inside it (different origin), and a reload
    // after a change should come back to the page the user was looking at
    // rather than dropping them at the front door.
    const path = route === "/" ? "" : route;
    const url = `${previewUrl}${path}`;
    return `${url}${url.includes("?") ? "&" : "?"}scio=${nudge}`;
  }, [previewUrl, route, nudge]);

  // --- the change --------------------------------------------------------
  const setNote = (key: string, note: string) =>
    setPending((prev) => prev.map((p) => (p.key === key ? { ...p, note } : p)));

  const remove = (key: string) => setPending((prev) => prev.filter((p) => p.key !== key));

  const generate = useCallback(
    async (batch: Pending[], text: string) => {
      setApplying(true);
      setNotice(null);
      try {
        const res = await api.applyDesignChange(projectId, {
          markings: batch.map((p) => ({
            scioId: p.hit.scio_id,
            scioPackage: p.hit.scio_package,
            tag: p.hit.tag,
            text: p.hit.text,
            ancestorId: p.hit.ancestor_id,
            ancestorPackage: p.hit.ancestor_package,
            ancestorDistance: p.hit.ancestor_distance,
            note: p.note,
          })),
          prompt: text,
        });
        setOutcome(res);
        setConflicts(res.conflicts);
        if (res.applied) {
          setPreview((prev) =>
            prev.kind === "ready" ? { ...prev, manifest: res.manifest } : prev,
          );
          // Only what was applied leaves the list. A marking the engine could
          // not address stays, so it can be reworded rather than lost.
          const skipped = new Set(res.skipped.map((s) => s.scioId));
          setPending(batch.filter((p) => skipped.has(p.hit.scio_id)));
          setPrompt("");
          bridgeRef.current?.clearMarks();
          setNudge((n) => n + 1);
          refreshVersions();
        }
        return res;
      } catch (err) {
        setNotice(err instanceof ApiError ? err.message : "The change could not be applied.");
        return null;
      } finally {
        setApplying(false);
      }
    },
    [api, projectId, refreshVersions],
  );

  /** "Keep it as-is": the marking that raised the question goes, the rest stay. */
  function keepAsIs(conflict: DesignConflict) {
    if (conflict.scioId) {
      setPending((prev) => prev.filter((p) => p.hit.scio_id !== conflict.scioId));
    } else {
      // No id means it was the free prompt that argued with the spec.
      setPrompt("");
    }
    setConflicts((prev) => prev.filter((c) => c !== conflict));
    setConfirming(null);
  }

  /** "Change the plan": a real amendment to the approved spec, then re-apply. */
  async function changeThePlan(conflict: DesignConflict) {
    setConfirming(null);
    setApplying(true);
    try {
      await api.amendSpec(projectId, {
        kind: conflict.kind as "non_goal" | "auth" | "access",
        specSays: conflict.specSays,
        note: conflict.note,
      });
    } catch (err) {
      setNotice(err instanceof ApiError ? err.message : "The spec could not be changed.");
      setApplying(false);
      return;
    }
    setApplying(false);
    setConflicts((prev) => prev.filter((c) => c !== conflict));
    await generate(pending, prompt);
  }

  async function returnTo(version: DesignVersion) {
    setRestoring(version.id);
    setNotice(null);
    try {
      const res = await api.restoreDesignVersion(projectId, version.id);
      if (!res.restored) {
        setNotice(res.error);
        return;
      }
      setPreview((prev) =>
        prev.kind === "ready" ? { ...prev, manifest: res.manifest } : prev,
      );
      setPending([]);
      setOutcome(null);
      setConflicts([]);
      bridgeRef.current?.clearMarks();
      setNudge((n) => n + 1);
      refreshVersions();
    } catch (err) {
      setNotice(err instanceof ApiError ? err.message : "That version could not be restored.");
    } finally {
      setRestoring(null);
    }
  }

  // --- render ------------------------------------------------------------
  // One branch per state, and the compiler checks there are no others. The
  // condition this replaces — `preparing || (!previewUrl && !error)` — was the
  // render deducing which of six flags it was holding (B090).
  if (preview.kind === "disconnected") {
    return (
      <section>
        <Eyebrow>Design · preparing</Eyebrow>
        <PageTitle>Building a preview you can mark up</PageTitle>
        <StateCard
          icon="~"
          tone="warn"
          title="We lost the connection"
          action={<Button onClick={checkOnPreview}>Check on it</Button>}
        >
          The preview is still being built on the server — this page just stopped hearing about
          it.
        </StateCard>
      </section>
    );
  }

  if (preview.kind === "failed") {
    // Its own screen, because there is no preview to put a card above. This is
    // the branch the old flags did not have: a failed preview fell through to
    // the main render, which drew an app frame around a `previewUrl` of null.
    return (
      <section>
        <Eyebrow>Design</Eyebrow>
        <PageTitle>The preview could not be built</PageTitle>
        <StateCard
          icon="!"
          tone="error"
          title="Something didn't work"
          action={<Button onClick={rebuild}>Try again</Button>}
        >
          {preview.message}
        </StateCard>
      </section>
    );
  }

  if (preview.kind === "preparing") {
    const lines = preview.lines;
    return (
      <section>
        <Eyebrow>Design · preparing</Eyebrow>
        <PageTitle>Building a preview you can mark up</PageTitle>
        <Lede>
          This is a real build, so you can click it — only the parts you mark get rebuilt
          afterwards.
        </Lede>
        <div className="bg-surface border border-line rounded-card p-[18px]">
          <div className="font-mono text-[11px] text-muted" data-testid="design-log">
            {lines.length === 0 && <div className="py-0.5">Working out what to build…</div>}
            {lines.slice(-8).map((line, i) => (
              <div key={`${line}-${i}`} className="py-0.5">
                {line}
              </div>
            ))}
          </div>
        </div>
      </section>
    );
  }

  return (
    <section>
      <div className="flex items-start justify-between gap-4 flex-wrap">
        <div>
          <Eyebrow>Design · preview</Eyebrow>
          <PageTitle>Shape the design</PageTitle>
        </div>
        <div className="flex items-center gap-2 mt-2">
          <div className="inline-flex rounded-btn border border-line overflow-hidden">
            {(["use", "mark"] as const).map((value) => (
              <button
                key={value}
                type="button"
                onClick={() => setMode(value)}
                aria-pressed={mode === value}
                className={`text-sm px-4 py-2 cursor-pointer border-0 ${
                  mode === value ? "bg-teal text-on-teal" : "bg-transparent text-muted"
                }`}
              >
                {value === "use" ? "Use" : "Mark"}
              </button>
            ))}
          </div>
          <Button onClick={() => navigate(`/projects/${projectId}/build`)}>Build it →</Button>
        </div>
      </div>

      <Lede>
        {mode === "mark"
          ? "Click anything in the preview to add it to your changes. The app won't react while you're marking."
          : "Use the preview like the real app. Switch to Mark to point at something you want changed."}
      </Lede>

      {notice && (
        <div className="mb-4">
          <StateCard
            icon="!"
            tone="error"
            title="Something didn't work"
            action={
              <Button variant="ghost" onClick={() => setNotice(null)}>
                Dismiss
              </Button>
            }
          >
            {notice}
          </StateCard>
        </div>
      )}

      {reachable === false && (
        <div
          className="text-xs text-attention border border-attention/40 rounded-btn px-3 py-2 mb-4 flex items-center gap-3 flex-wrap"
          data-testid="bridge-unreachable"
        >
          <span className="font-mono">
            The preview hasn't said hello, so clicking it won't add anything. Either it isn't
            running any more, or this page is on the wrong origin — the preview only talks to the
            origin Scio was configured with, and this page is on {window.location.origin}.
          </span>
          {/* A preview that stopped is the common case, and without this the
              window is a dead iframe with no way out of it. */}
          <Button variant="ghost" className="!px-3 !py-1" onClick={() => void rebuild()}>
            Build the preview again
          </Button>
        </div>
      )}

      <div className="grid grid-cols-[1fr_340px] max-md:grid-cols-1 gap-[18px]">
        <div className="bg-surface border border-line rounded-card overflow-hidden">
          <div className="flex items-center gap-2 px-3 py-2 border-b border-line bg-surface-2">
            <span className="w-2.5 h-2.5 rounded-full bg-line-strong" />
            <span className="w-2.5 h-2.5 rounded-full bg-line-strong" />
            <span className="w-2.5 h-2.5 rounded-full bg-line-strong" />
            <span className="font-mono text-[11px] text-muted ml-2 truncate">
              {previewUrl ?? "no preview"}
              {route !== "/" && <span className="text-ink">{route}</span>}
            </span>
          </div>
          {routes.length > 1 && (
            <div
              className="flex items-center gap-1 flex-wrap px-3 py-2 border-b border-line"
              data-testid="routes"
            >
              {routes.map((candidate) => (
                <button
                  key={candidate}
                  type="button"
                  aria-pressed={candidate === route}
                  onClick={() => setRoute(candidate)}
                  className={`font-mono text-[11px] px-2 py-1 rounded-btn border cursor-pointer ${
                    candidate === route
                      ? "bg-teal text-on-teal border-teal"
                      : "bg-transparent text-muted border-line"
                  }`}
                >
                  {candidate}
                </button>
              ))}
            </div>
          )}
          {previewUrl ? (
            <iframe
              ref={frameRef}
              key={frameSrc}
              title="Your app"
              src={frameSrc}
              onLoad={() => {
                setLoaded(true);
                bridgeRef.current?.ping();
              }}
              className="w-full h-[560px] border-0 bg-white"
            />
          ) : (
            <div className="h-[560px] flex items-center justify-center text-[13px] text-muted">
              The preview isn't running right now.
            </div>
          )}
        </div>

        <aside className="flex flex-col gap-[18px]">
          <div className="bg-surface border border-line rounded-card p-[18px]">
            <div className="font-mono text-[11px] uppercase tracking-[0.14em] text-muted mb-2.5">
              Your changes {pending.length > 0 && `(${pending.length})`}
            </div>

            {pending.length === 0 && (
              <p className="text-[13px] text-muted">
                Switch to <b>Mark</b> and click the preview to add a change.
              </p>
            )}

            <ol className="flex flex-col gap-2.5">
              {pending.map((item, index) => {
                const at = locate(manifest, item.hit.scio_id);
                return (
                  <li key={item.key} className="border border-line rounded-btn p-2.5">
                    <div className="flex items-start gap-2">
                      <span className="font-mono text-[11px] text-teal mt-1">{index + 1}</span>
                      <div className="flex-1 min-w-0">
                        <div className="text-[13px] truncate">
                          {item.hit.text || `<${item.hit.tag}>`}
                        </div>
                        {at ? (
                          <div className="font-mono text-[10px] text-muted truncate">
                            {readableId(at.package)} · {at.where}
                            {/* Which page it was on: once the preview has more
                                than one, "the button" is ambiguous without it. */}
                            {item.route && item.route !== "/" ? ` · ${item.route}` : ""}
                          </div>
                        ) : (
                          <div className="text-[11px] text-attention" data-testid="unaddressable">
                            Scio can't address this one — it has no marker of its own
                            {item.hit.ancestor_id ? `, only ${item.hit.ancestor_id} around it` : ""}.
                            Try clicking the thing itself.
                          </div>
                        )}
                      </div>
                      <button
                        type="button"
                        onClick={() => remove(item.key)}
                        aria-label={`Remove change ${index + 1}`}
                        className="text-muted hover:text-ink text-sm cursor-pointer bg-transparent border-0"
                      >
                        ×
                      </button>
                    </div>
                    <input
                      value={item.note}
                      onChange={(e) => setNote(item.key, e.target.value)}
                      placeholder="What should change here?"
                      aria-label={`Note for change ${index + 1}`}
                      className="w-full mt-2 bg-surface-2 border border-line rounded-btn px-2.5 py-1.5 text-[13px]"
                    />
                  </li>
                );
              })}
            </ol>

            <label className="block font-mono text-[11px] uppercase tracking-[0.14em] text-muted mt-4 mb-1.5">
              Anything else
            </label>
            <textarea
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              placeholder="Describe any change in words…"
              aria-label="Anything else"
              className="w-full h-[72px] bg-surface-2 border border-line rounded-btn px-2.5 py-2 text-[13px] resize-y"
            />

            <Button
              className="w-full justify-center mt-3"
              disabled={applying || (pending.length === 0 && !prompt.trim())}
              onClick={() => void generate(pending, prompt)}
            >
              {applying ? "Generating…" : "Generate again"}
            </Button>
          </div>

          {conflicts.length > 0 && (
            <div
              className="bg-surface border border-attention/50 rounded-card p-[18px]"
              data-testid="conflicts"
            >
              <div className="font-mono text-[11px] uppercase tracking-[0.14em] text-attention mb-2.5">
                Needs your call — nothing was built
              </div>
              {conflicts.map((conflict) => (
                <div key={conflict.question} className="py-2 border-b border-line last:border-0">
                  <p className="text-[13px] leading-relaxed">{conflict.question}</p>
                  <p className="text-[12px] text-muted mt-1">You said: {conflict.specSays}</p>
                  {confirming === conflict ? (
                    <div className="mt-2.5 border border-attention/50 rounded-btn p-2.5">
                      <p className="text-[12px] leading-relaxed">
                        This drops a protection Scio worked out for you: <b>{conflict.specSays}</b>.
                        It stays on the record as something you allowed, and the rest of the app is
                        still built to protect this data. If the app should work a different way
                        altogether, change it in the wizard instead.
                      </p>
                      <div className="flex gap-2 mt-2.5">
                        <Button onClick={() => void changeThePlan(conflict)} disabled={applying}>
                          Yes, allow it
                        </Button>
                        <Button variant="ghost" onClick={() => setConfirming(null)}>
                          Cancel
                        </Button>
                      </div>
                    </div>
                  ) : (
                    <div className="flex gap-2 mt-2.5 flex-wrap">
                      <Button variant="ghost" onClick={() => keepAsIs(conflict)}>
                        Keep it as-is
                      </Button>
                      <Button
                        onClick={() =>
                          isSecurity(conflict)
                            ? setConfirming(conflict)
                            : void changeThePlan(conflict)
                        }
                        disabled={applying}
                      >
                        Change the plan
                      </Button>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}

          {/* Shown whenever the engine said anything about packages or skipped
              markings — not only on success. A package the guardrails rejected
              is exactly the thing that must not disappear from the screen. */}
          {outcome && (outcome.packages.length > 0 || outcome.skipped.length > 0) && (
            <div className="bg-surface border border-line rounded-card p-[18px]" data-testid="outcome">
              <div className="font-mono text-[11px] uppercase tracking-[0.14em] text-muted mb-2.5">
                {outcome.applied ? "What changed" : "Nothing was applied"}
              </div>
              {outcome.packages.map((change) => (
                <div key={change.package} className="text-[13px] py-1">
                  <span className={change.accepted ? "text-verified" : "text-danger"}>
                    {change.accepted ? "✓" : "×"}
                  </span>{" "}
                  {readableId(change.package)}
                  {change.accepted ? (
                    <span className="text-muted">
                      {" "}
                      — {change.editedFiles.join(", ")} ({change.unchangedFiles} other files
                      untouched)
                    </span>
                  ) : (
                    <span className="text-muted"> — {change.rejection}</span>
                  )}
                </div>
              ))}
              {outcome.skipped.length > 0 && (
                <ul className="mt-2 pt-2 border-t border-line flex flex-col gap-1">
                  {outcome.skipped.map((skip, i) => (
                    <li key={`${skip.scioId}-${i}`} className="text-[12px] text-attention">
                      Skipped “{skip.note || "no note"}” — {skip.error}
                    </li>
                  ))}
                </ul>
              )}
            </div>
          )}

          {versions.length > 0 && (
            <div className="bg-surface border border-line rounded-card p-[18px]" data-testid="versions">
              <div className="font-mono text-[11px] uppercase tracking-[0.14em] text-muted mb-2.5">
                Versions
              </div>
              {versions.map((version) => {
                const ref = parseRef(version);
                return (
                  <div key={version.id} className="py-2 border-b border-line last:border-0">
                    <div className="flex items-baseline justify-between gap-2">
                      <span className="font-mono text-[11px] text-muted">v{version.number}</span>
                      {version.isCurrent && (
                        <span className="font-mono text-[10px] text-verified">now showing</span>
                      )}
                    </div>
                    <p className="text-[12px] text-muted whitespace-pre-wrap mt-0.5">
                      {ref.change || "a change"}
                    </p>
                    {!version.isCurrent && ref.gitSha && (
                      <Button
                        variant="ghost"
                        className="mt-1.5 !px-2.5 !py-1 text-xs"
                        disabled={restoring !== null}
                        onClick={() => void returnTo(version)}
                      >
                        {restoring === version.id ? "Returning…" : "Return to this version"}
                      </Button>
                    )}
                  </div>
                );
              })}
            </div>
          )}

          {whole && (
            <div className="bg-surface border border-line rounded-card p-[18px]">
              <div className="font-mono text-[11px] uppercase tracking-[0.14em] text-muted mb-2">
                What you're building
              </div>
              <p className="text-[13px] leading-relaxed whitespace-pre-wrap">{whole}</p>
            </div>
          )}
        </aside>
      </div>
    </section>
  );
}
