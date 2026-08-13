import type { IntakeStepResponse } from "@scio/shared";
import { useCallback, useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { Button, Eyebrow, Lede, PageTitle, StateCard } from "../components/ui";
import { ApiError } from "../lib/api";
import { assumptionRows, specRows } from "../lib/spec";
import { useApi } from "../lib/useApi";

/**
 * The spec gate: "so if I've understood you right…".
 *
 * Two things are load-bearing. The assumptions are shown as assumptions — the
 * user should never discover later that Scio decided something quietly. And the
 * size signal is labelled rough, because it is a part count, not a price: the
 * real cost formula is a later step, and a number the product cannot stand
 * behind would be worse than no number.
 */
export function SpecPage() {
  const { projectId = "" } = useParams();
  const api = useApi();
  const navigate = useNavigate();

  const [step, setStep] = useState<IntakeStepResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [approving, setApproving] = useState(false);
  const [locked, setLocked] = useState<{ number: number } | null>(null);

  const load = useCallback(() => {
    setError(null);
    api
      .getIntake(projectId)
      .then(setStep)
      .catch((err) => setError(err instanceof ApiError ? err.message : "Something went wrong"));
  }, [api, projectId]);

  useEffect(load, [load]);

  async function approve() {
    setApproving(true);
    setError(null);
    try {
      const res = await api.approveSpec(projectId);
      setLocked({ number: res.specVersion.number });
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Something went wrong");
    } finally {
      setApproving(false);
    }
  }

  if (locked) {
    return (
      <section>
        <Eyebrow>Gate 1 · passed</Eyebrow>
        <PageTitle>Spec locked</PageTitle>
        <Lede>Version {locked.number} is frozen — this is what your build will be held to.</Lede>
        <StateCard
          icon="✓"
          title="Build is next"
          action={<Button onClick={() => navigate("/projects")}>Back to projects</Button>}
        >
          Your spec is saved as a version you can always come back to. Building from it is the next
          step — it isn't wired up yet.
        </StateCard>
      </section>
    );
  }

  const spec = step?.updated_spec ?? {};
  const assumptions = assumptionRows(spec);
  const rows = specRows(spec);

  return (
    <section>
      <Eyebrow>Review · spec</Eyebrow>
      <PageTitle>So if I've understood you right…</PageTitle>
      <Lede>Here's your app, in my words. Check it — especially the assumptions.</Lede>

      {error && (
        <div className="mb-4">
          <StateCard icon="!" tone="error" title="Something went wrong" action={<Button variant="ghost" onClick={load}>Retry</Button>}>
            {error}
          </StateCard>
        </div>
      )}

      <div className="bg-surface border border-line rounded-card p-[22px] relative">
        <span className="absolute top-3 left-3 w-2.5 h-2.5 border-t-[1.5px] border-l-[1.5px] border-line-strong" />

        {/* The narrative is the confirmation; the fields are the detail. Both
            are shown — the spec is what gets frozen, so it is never hidden
            behind prose that may not have been available this run. */}
        {step?.whole && (
          <p className="text-[15px] leading-[1.7] whitespace-pre-wrap mb-5">{step.whole}</p>
        )}

        <p className="text-[13px] text-muted mb-2">
          {step?.whole ? "In detail:" : "Here's what I have, field by field."}
        </p>
        <div>
          {rows.map((row) => (
            <div
              key={row.field}
              className="flex justify-between gap-4 py-2 border-b border-line last:border-0"
            >
              <span className="text-[12px] text-muted flex-none max-w-[38%]">{row.label}</span>
              <span className="text-[14px] text-right">{row.value}</span>
            </div>
          ))}
        </div>

        {assumptions.length > 0 && (
          <div className="mt-5 pt-4 border-t border-line">
            <div className="font-mono text-[11px] uppercase tracking-[0.1em] text-muted mb-2">
              Assumptions I made
            </div>
            <ul className="flex flex-col gap-1.5">
              {assumptions.map((row) => (
                <li key={row.field} className="text-[13px]">
                  <span className="font-mono text-[9.5px] text-attention border border-attention/40 rounded px-1.5 py-px mr-2">
                    assumed
                  </span>
                  {row.label}: {row.value}
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>

      {step?.estimate && (
        <p className="font-mono text-xs text-muted mt-3.5">
          Roughly {step.estimate.parts} parts to build — a rough signal, not a price. The real
          estimate comes later.
        </p>
      )}
      {step?.engine.degraded?.length ? (
        <p className="font-mono text-xs text-muted mt-1.5">
          Showing your spec directly — the written summary wasn't available for this run.
        </p>
      ) : null}

      <div className="flex gap-2.5 justify-end mt-5 max-sm:flex-col">
        <Button variant="ghost" onClick={() => navigate(`/projects/${projectId}/wizard`)}>
          No — let me adjust
        </Button>
        <Button variant="ghost" onClick={() => navigate("/projects")}>
          Not now
        </Button>
        <Button onClick={() => void approve()} disabled={approving || !step}>
          {approving ? "Freezing…" : "Yes, build it →"}
        </Button>
      </div>
    </section>
  );
}
