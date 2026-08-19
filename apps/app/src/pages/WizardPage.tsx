import type { IntakeSpec, IntakeStepResponse, WizardTurn } from "@scio/shared";
import { useCallback, useEffect, useRef, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { Button, Eyebrow, Lede, PageTitle, StateCard } from "../components/ui";
import { ApiError } from "../lib/api";
import { coreProgress, specRows } from "../lib/spec";
import { useApi } from "../lib/useApi";

/**
 * Gate 1's conversation. Every turn is a round trip through the API to the
 * engine: what they wrote is extracted into the spec, and the panel beside the
 * chat fills in as it happens.
 *
 * The panel is not decoration — it is the promise that Scio is *listening*
 * rather than collecting text, which is what makes the review screen believable
 * when it arrives.
 */

function Bubble({ turn }: { turn: WizardTurn }) {
  const scio = turn.role === "scio";
  return (
    <div className={`flex gap-2.5 mb-4 ${scio ? "" : "flex-row-reverse"}`}>
      {scio && (
        <span className="w-[26px] h-[26px] rounded-[7px] bg-teal text-on-teal font-display font-semibold text-[13px] flex items-center justify-center flex-none">
          S
        </span>
      )}
      <div
        className={`max-w-[80%] rounded-card px-3.5 py-2.5 text-[14px] leading-relaxed border ${
          scio ? "bg-surface border-line" : "bg-surface-2 border-line-strong"
        }`}
      >
        <p className="whitespace-pre-wrap">{turn.example ? stripExample(turn.text, turn.example) : turn.text}</p>
        {turn.example && (
          <div className="font-mono text-[11px] text-muted mt-1.5">Ex: “{turn.example}”</div>
        )}
      </div>
    </div>
  );
}

/** The example is stored inside the message text so a reload keeps it; the
 * bubble shows it separately, so it is removed from the sentence here. */
function stripExample(text: string, example: string): string {
  const marker = `For example: ${example}`;
  return text.endsWith(marker) ? text.slice(0, -marker.length).trim() : text;
}

function WholenessPanel({
  spec,
  buildable,
  loading,
  onContinue,
}: {
  spec: IntakeSpec;
  buildable: boolean;
  /** Nothing has come back yet. NOT the same as "nothing has been answered",
   *  which is what this panel used to claim during the wait — the first real
   *  run showed a fully-specced project "0 of 6 core answers" for twelve
   *  seconds, with Continue disabled. A screen whose whole job is to reflect
   *  the user's answers back must never state a number it does not have. */
  loading: boolean;
  onContinue: () => void;
}) {
  const rows = specRows(spec);
  const { answered, total } = coreProgress(spec);
  const percent = Math.round((answered / total) * 100);

  if (loading) {
    return (
      <aside
        className="bg-surface border border-line rounded-card p-[18px] relative self-start"
        data-testid="wholeness-loading"
      >
        <span className="absolute top-3 left-3 w-2.5 h-2.5 border-t-[1.5px] border-l-[1.5px] border-line-strong" />
        <div className="font-mono text-[11px] uppercase tracking-[0.14em] text-muted mb-3.5">
          Your app so far
        </div>
        <p className="text-[13px] text-muted">Reading your project…</p>
      </aside>
    );
  }

  return (
    <aside className="bg-surface border border-line rounded-card p-[18px] relative self-start">
      <span className="absolute top-3 left-3 w-2.5 h-2.5 border-t-[1.5px] border-l-[1.5px] border-line-strong" />
      <div className="font-mono text-[11px] uppercase tracking-[0.14em] text-muted mb-3.5">
        Your app so far
      </div>

      {rows.length === 0 && (
        <p className="text-[13px] text-muted">Nothing yet — answer the first question.</p>
      )}

      {rows.map((row) => (
        <div key={row.field} className="flex justify-between gap-3 py-[7px] border-b border-line last:border-0">
          <span className="text-[12px] text-muted flex-none max-w-[42%]">{row.label}</span>
          <span className="text-[13px] text-right">
            {row.value}
            {row.assumed && (
              <span className="font-mono text-[9.5px] text-attention border border-attention/40 rounded px-1.5 py-px ml-1.5">
                assumed
              </span>
            )}
            {row.derived && (
              <span className="font-mono text-[9.5px] text-muted border border-line-strong rounded px-1.5 py-px ml-1.5">
                inferred
              </span>
            )}
          </span>
        </div>
      ))}

      <div className="font-mono text-[11px] text-muted mt-4">
        {buildable ? "Buildable enough" : `${answered} of ${total} core answers`}
        <div className="h-1 bg-surface-2 rounded-full mt-1.5 overflow-hidden">
          <i className="block h-full bg-teal rounded-full" style={{ width: `${percent}%` }} />
        </div>
      </div>

      <Button className="mt-4 w-full justify-center" disabled={!buildable} onClick={onContinue}>
        Continue to review →
      </Button>
    </aside>
  );
}

export function WizardPage() {
  const { projectId = "" } = useParams();
  const api = useApi();
  const navigate = useNavigate();

  const [step, setStep] = useState<IntakeStepResponse | null>(null);
  const [draft, setDraft] = useState("");
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const logRef = useRef<HTMLDivElement>(null);

  const load = useCallback(() => {
    setError(null);
    api
      .getIntake(projectId)
      .then(setStep)
      .catch((err) => setError(err instanceof ApiError ? err.message : "Something went wrong"));
  }, [api, projectId]);

  useEffect(load, [load]);

  useEffect(() => {
    // scrollTop rather than scrollTo: the same effect, and it exists everywhere
    // the component runs (jsdom included).
    if (logRef.current) logRef.current.scrollTop = logRef.current.scrollHeight;
  }, [step?.messages.length]);

  async function send() {
    const text = draft.trim();
    if (!text || sending) return;
    setSending(true);
    setError(null);
    try {
      const next = await api.sendIntakeMessage(projectId, text);
      setStep(next);
      setDraft("");
      if (next.buildable) navigate(`/projects/${projectId}/spec`);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Something went wrong");
    } finally {
      setSending(false);
    }
  }

  const spec = step?.updated_spec ?? {};
  const contradiction = step?.contradictions?.[0];

  return (
    <section>
      <Eyebrow>New app · guided setup</Eyebrow>
      <PageTitle>Let's shape your app</PageTitle>
      <Lede>A few quick questions — answer in your own words. Scio structures it as you go.</Lede>

      {error && (
        <div className="mb-4">
          <StateCard
            icon="!"
            tone="error"
            title="That didn't get through"
            action={
              <Button variant="ghost" onClick={load}>
                Reload the conversation
              </Button>
            }
          >
            {error}
          </StateCard>
        </div>
      )}

      <div className="grid grid-cols-[1fr_300px] max-md:grid-cols-1 gap-[18px]">
        <div className="bg-surface border border-line rounded-card p-[18px] flex flex-col">
          <div ref={logRef} className="max-h-[420px] overflow-y-auto pr-1" data-testid="chatlog">
            {(step?.messages.length ?? 0) === 0 && (
              <Bubble
                turn={{
                  id: "opening",
                  role: "scio",
                  text: "Hi! What should the app do?",
                  example: "Lets guests book a table and pick a time.",
                }}
              />
            )}
            {step?.messages.map((turn) => (
              <Bubble key={turn.id} turn={turn} />
            ))}
          </div>

          {contradiction && (
            <div className="border border-attention/40 bg-attention/10 rounded-card px-3.5 py-2.5 text-[13px] mb-3">
              <span className="font-mono text-[10px] uppercase tracking-[0.1em] text-attention">
                Needs your call
              </span>
              <p className="mt-1">{contradiction.description}</p>
            </div>
          )}

          <div className="flex gap-2 items-end border-t border-line pt-3 mt-2">
            <textarea
              aria-label="Your answer"
              className="flex-1 border-none bg-transparent resize-none font-sans text-[14px] text-ink min-h-[44px] focus:outline-none placeholder:text-muted"
              placeholder="Type your answer…"
              value={draft}
              disabled={sending}
              onChange={(e) => setDraft(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  void send();
                }
              }}
            />
            <Button onClick={() => void send()} disabled={sending || !draft.trim()}>
              {sending ? "Thinking…" : "Send →"}
            </Button>
          </div>
        </div>

        <WholenessPanel
          spec={spec}
          buildable={step?.buildable ?? false}
          loading={step === null && error === null}
          onContinue={() => navigate(`/projects/${projectId}/spec`)}
        />
      </div>
    </section>
  );
}
