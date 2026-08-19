import type { BuildEstimate, CorrectSpecFieldRequest, IntakeStepResponse } from "@scio/shared";
import { useCallback, useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { Button, Eyebrow, Lede, PageTitle, StateCard } from "../components/ui";
import { ApiError } from "../lib/api";
import {
  CORRECTABLE_FIELDS,
  type FieldKind,
  assumptionRows,
  editText,
  kindOf,
  labelFor,
  readSensitivity,
  specRows,
  toValue,
} from "../lib/spec";
import { useApi } from "../lib/useApi";

/**
 * The spec gate: "so if I've understood you right…".
 *
 * Three things are load-bearing. The assumptions are shown as assumptions — the
 * user should never discover later that Scio decided something quietly. The
 * estimate is shown as a RANGE for the base build, with what it excludes said
 * out loud: this is the answer to credit-anxiety, and a false-exact figure the
 * build then exceeds would do more damage than no figure at all.
 *
 * And every field is EDITABLE here (B066). Showing someone that their answer was
 * filed under the wrong heading, with no way to fix it short of starting over,
 * is worse than not showing it: they approve it anyway, and the whole stack
 * faithfully builds the wrong thing. A correction is one action, it outranks
 * extraction, and it is re-validated — so a correction that opens new work says
 * so and holds this screen's own gate shut until it is answered.
 */
export function SpecPage() {
  const { projectId = "" } = useParams();
  const api = useApi();
  const navigate = useNavigate();

  const [step, setStep] = useState<CorrectableStep | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [approving, setApproving] = useState(false);
  const [editing, setEditing] = useState<string | null>(null);
  const [saving, setSaving] = useState<string | null>(null);
  const [opened, setOpened] = useState<string[]>([]);

  const load = useCallback(() => {
    setError(null);
    api
      .getIntake(projectId)
      .then(setStep)
      .catch((err) => setError(err instanceof ApiError ? err.message : "Something went wrong"));
  }, [api, projectId]);

  useEffect(load, [load]);

  /**
   * One correction, applied and re-validated.
   *
   * The whole response replaces the page's state rather than patching the row:
   * the narrative, the assumptions and the estimate are all derived from the
   * spec, and a screen showing a summary of a spec that no longer exists is
   * exactly the kind of quiet wrongness this screen exists to prevent.
   */
  async function save(body: CorrectSpecFieldRequest) {
    setSaving(body.field);
    setError(null);
    try {
      const next = await api.correctSpecField(projectId, body);
      setStep(next);
      setEditing(null);
      setOpened(next.newly_required ?? []);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Something went wrong");
    } finally {
      setSaving(null);
    }
  }

  async function approve() {
    setApproving(true);
    setError(null);
    try {
      // The whole is what they are approving, so it is frozen with the spec.
      await api.approveSpec(projectId, step?.whole ?? undefined);
      // One question stands between the spec and the build: shape the design
      // first, or build straight away. It is asked here rather than assumed
      // because a change made against a preview costs one package, and the same
      // change made after a full build costs the build.
      navigate(`/projects/${projectId}/involve`);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Something went wrong");
      setApproving(false);
    }
  }

  const spec = step?.updated_spec ?? {};
  const assumptions = assumptionRows(spec);
  const rows = specRows(spec);
  const gate = step?.gate;
  const stillNeeded = [...(gate?.missing_core ?? []), ...(gate?.unresolved_conditionals ?? [])];
  const conflicts = step?.contradictions ?? [];
  const held = Boolean(step) && step?.buildable === false;

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
          {rows.map((row) =>
            editing === row.field ? (
              <FieldEditor
                key={row.field}
                field={row.field}
                value={(spec[row.field] as { value?: unknown } | undefined)?.value}
                busy={saving === row.field}
                onCancel={() => setEditing(null)}
                onSave={save}
              />
            ) : (
              <div
                key={row.field}
                className="flex justify-between items-baseline gap-4 py-2 border-b border-line last:border-0 group"
                data-testid={`row-${row.field}`}
              >
                <span className="text-[12px] text-muted flex-none max-w-[38%]">{row.label}</span>
                <span className="flex items-baseline gap-2.5 text-right">
                  <span className="text-[14px]">{row.value}</span>
                  <button
                    type="button"
                    onClick={() => setEditing(row.field)}
                    className="font-mono text-[11px] text-muted hover:text-teal underline decoration-dotted underline-offset-2 flex-none"
                    aria-label={`Correct ${row.label}`}
                  >
                    correct
                  </button>
                </span>
              </div>
            ),
          )}
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

      {(stillNeeded.length > 0 || conflicts.length > 0) && (
        <div
          className="mt-4 border border-attention/40 rounded-card p-[18px]"
          data-testid="still-needed"
        >
          <div className="font-mono text-[11px] uppercase tracking-[0.1em] text-attention mb-2">
            {opened.length > 0 ? "That change needs a bit more" : "Before this can be built"}
          </div>
          <p className="text-[13px] text-muted mb-3.5">
            {opened.length > 0
              ? `Correcting ${labelFor(step?.changed?.[0] ?? "")} opened this. Answer it here — you don't have to go back to the wizard.`
              : "Answer these here and the gate opens. No need to start the wizard again."}
          </p>

          {conflicts.map((conflict) => (
            <p key={conflict.description} className="text-[13px] mb-3">
              <span className="font-mono text-[9.5px] text-attention border border-attention/40 rounded px-1.5 py-px mr-2">
                disagrees
              </span>
              {conflict.description} — correct{" "}
              {conflict.fields.map((f) => labelFor(f)).join(" or ")} above.
            </p>
          ))}

          {stillNeeded.map((field) => (
            <FieldEditor
              key={field}
              field={field}
              value={(spec[field] as { value?: unknown } | undefined)?.value}
              busy={saving === field}
              onSave={save}
              alwaysOpen
            />
          ))}
        </div>
      )}

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
        <Button
          onClick={() => void approve()}
          disabled={approving || !step || held}
          title={held ? "Answer what's still needed above first." : undefined}
        >
          {approving ? "Freezing…" : "Yes, build it →"}
        </Button>
      </div>
    </section>
  );
}


/**
 * A turn, possibly a correction.
 *
 * `getIntake` and `correctSpecField` return the same screen's worth of state;
 * only a correction carries what it changed and what it opened. Modelling that
 * as optional keeps one piece of state on the page instead of two that can
 * disagree about which spec is current.
 */
type CorrectableStep = IntakeStepResponse & {
  newly_required?: string[];
  changed?: string[];
  cleared?: string[];
};

/**
 * Correcting one field.
 *
 * Three things it deliberately does:
 *
 * - **It offers the right control for the shape.** A list is typed as a list
 *   and split here; the sensitivity field gets its three parts rather than a
 *   JSON blob nobody can be expected to type.
 * - **It can move an answer.** "Belongs under" is the actual defect this whole
 *   feature exists for — "guests and staff" filed under what the app manages.
 *   Choosing a different field sets it there and empties this one, in ONE
 *   request, so the spec is never briefly holding the same answer twice.
 * - **It refuses nothing itself.** The engine owns what a field may contain and
 *   says which field was wrong; validating shapes in two languages is how the
 *   two definitions drift apart.
 */
function FieldEditor({
  field,
  value,
  busy,
  onSave,
  onCancel,
  alwaysOpen = false,
}: {
  field: string;
  value: unknown;
  busy: boolean;
  onSave: (body: CorrectSpecFieldRequest) => void | Promise<void>;
  onCancel?: () => void;
  alwaysOpen?: boolean;
}) {
  const kind: FieldKind = kindOf(field, value);
  const [target, setTarget] = useState(field);
  const [text, setText] = useState(() => editText(value, kind));
  const sensitivity = readSensitivity(value);
  const [owner, setOwner] = useState(sensitivity.owner);
  const [sensitive, setSensitive] = useState(sensitivity.sensitive);
  const [kinds, setKinds] = useState(sensitivity.kinds.join(", "));

  const moved = target !== field;
  // The shape follows where the answer is GOING, not where it came from: moving
  // "guests, staff" out of a list field into a sentence field must send a
  // sentence, or the engine refuses a correction the user got right.
  const outgoing: FieldKind = moved ? kindOf(target) : kind;

  function submit() {
    const body: CorrectSpecFieldRequest =
      outgoing === "sensitivity"
        ? {
            field: target,
            value: {
              owner: owner.trim() || "you",
              sensitive,
              kinds: kinds
                .split(",")
                .map((k) => k.trim())
                .filter(Boolean),
            },
          }
        : { field: target, value: toValue(text, outgoing) };
    if (moved) body.clear = [field];
    void onSave(body);
  }

  return (
    <div
      className="py-3 border-b border-line last:border-0"
      data-testid={`editor-${field}`}
    >
      <div className="font-mono text-[11px] uppercase tracking-[0.1em] text-muted mb-2">
        {labelFor(field)}
      </div>

      {kind === "sensitivity" && !moved ? (
        <div className="flex flex-col gap-2">
          <label className="text-[12px] text-muted">
            Who owns the data
            <input
              value={owner}
              onChange={(e) => setOwner(e.target.value)}
              aria-label="Who owns the data"
              className="w-full mt-1 bg-surface-2 border border-line rounded-btn px-2.5 py-1.5 text-[14px] text-ink"
            />
          </label>
          <label className="flex items-center gap-2 text-[13px]">
            <input
              type="checkbox"
              checked={sensitive}
              onChange={(e) => setSensitive(e.target.checked)}
              aria-label="Some of it is sensitive"
            />
            Some of it is sensitive
          </label>
          {sensitive && (
            <label className="text-[12px] text-muted">
              What kind (comma separated)
              <input
                value={kinds}
                onChange={(e) => setKinds(e.target.value)}
                placeholder="personal, payment, health"
                aria-label="What kind"
                className="w-full mt-1 bg-surface-2 border border-line rounded-btn px-2.5 py-1.5 text-[14px] text-ink"
              />
            </label>
          )}
        </div>
      ) : (
        <>
          <input
            value={text}
            onChange={(e) => setText(e.target.value)}
            aria-label={labelFor(field)}
            placeholder={outgoing === "list" ? "one, two, three" : "…"}
            className="w-full bg-surface-2 border border-line rounded-btn px-2.5 py-1.5 text-[14px] text-ink"
          />
          {outgoing === "list" && (
            <p className="text-[11px] text-muted mt-1">Separate them with commas.</p>
          )}
        </>
      )}

      {!alwaysOpen && (
        <label className="block text-[11px] text-muted mt-2.5">
          Belongs under
          <select
            value={target}
            onChange={(e) => setTarget(e.target.value)}
            aria-label="Belongs under"
            className="ml-2 bg-surface-2 border border-line rounded-btn px-2 py-1 text-[12px] text-ink"
          >
            {CORRECTABLE_FIELDS.map((name) => (
              <option key={name} value={name}>
                {labelFor(name)}
              </option>
            ))}
          </select>
        </label>
      )}

      <div className="flex gap-2 mt-2.5">
        <Button onClick={submit} disabled={busy}>
          {busy ? "Saving…" : moved ? "Move it there" : "Save"}
        </Button>
        {onCancel && (
          <Button variant="ghost" onClick={onCancel} disabled={busy}>
            Cancel
          </Button>
        )}
      </div>
    </div>
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
