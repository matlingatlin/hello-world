import type { BuildEstimate, IntakeStepResponse } from "@scio/shared";
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
 * estimate is shown as a RANGE for the base build, with what it excludes said
 * out loud: this is the answer to credit-anxiety, and a false-exact figure the
 * build then exceeds would do more damage than no figure at all.
 */
export function SpecPage() {
  const { projectId = "" } = useParams();
  const api = useApi();
  const navigate = useNavigate();

  const [step, setStep] = useState<IntakeStepResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [approving, setApproving] = useState(false);

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
      // The whole is what they are approving, so it is frozen with the spec.
      await api.approveSpec(projectId, step?.whole ?? undefined);
      // Level 1: approval leads straight to the build. No detour — the user
      // said "build it", and a screen in between would only be ceremony.
      navigate(`/projects/${projectId}/build`);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Something went wrong");
      setApproving(false);
    }
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

      {step?.estimate && <Estimate estimate={step.estimate} />}
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


function money(value: number): string {
  return value < 10 ? `$${value.toFixed(2)}` : `$${Math.round(value)}`;
}

function composition(estimate: BuildEstimate): string {
  const parts = estimate.composition;
  if (!parts) return `${estimate.parts} parts`;
  if (!parts.assembled) return `${parts.parts_total} parts · all built`;
  return `${parts.parts_total} parts · ${parts.assembled} reused · ${parts.generated} built`;
}

/**
 * What the build costs, before it runs.
 *
 * Always a range and always "for the base build" — a package that needs a repair
 * round costs about twice one that passes first time, and which will is not
 * knowable in advance. When the engine could not price the plan we show the part
 * count alone rather than guessing.
 */
function Estimate({ estimate }: { estimate: BuildEstimate }) {
  const cost = estimate.cost_usd;
  const minutes = estimate.minutes;

  if (!cost || !minutes) {
    return (
      <p className="font-mono text-xs text-muted mt-3.5" data-testid="estimate">
        {composition(estimate)} — we couldn't price this build just now.
      </p>
    );
  }

  return (
    <div className="mt-3.5 border border-line rounded-card p-3.5" data-testid="estimate">
      <p className="font-mono text-[13px]">
        ~{money(cost.low)}–{money(cost.high)} · ~{Math.round(minutes.low)}–
        {Math.round(minutes.high)} min
      </p>
      <p className="font-mono text-[11px] text-muted mt-1.5">{composition(estimate)}</p>
      <p className="text-[12px] text-muted mt-2 leading-relaxed">
        For the base build. Every change you make afterwards adds — and you only pay once you
        approve.
      </p>
    </div>
  );
}
