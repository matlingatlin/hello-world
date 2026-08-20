import type { LatestBuildResponse } from "@scio/shared";
import { useCallback, useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { Button, Eyebrow, Lede, PageTitle, StateCard } from "../components/ui";
import { ApiError } from "../lib/api";
import { useApi } from "../lib/useApi";

/**
 * The reveal: the app they asked for, running, with the truth about it.
 *
 * The trust receipt is the point of the screen. Anyone can show a green tick;
 * showing "this works, and these two parts need a look" is what makes the tick
 * mean anything. So the parts that need a look and the parts that were never
 * built are rendered from the same record, at the same size, as the good news.
 */

/** What a build spent. Always two decimals: "$0" would read as free rather than
 *  cheap, and cheap-but-not-free is the honest answer for most builds. */
function spent(value: number): string {
  return `$${Math.max(0, value).toFixed(2)}`;
}

/** "estimated ~$1.05–$2.51 · " — or nothing, when there is no estimate to
 *  compare against. Inventing one to fill the gap is the failure this whole
 *  line exists to prevent. */
function estimated(estimate: LatestBuildResponse["estimate"]): string {
  const cost = estimate?.cost_usd;
  if (!cost) return "";
  return `estimated ~${spent(cost.low)}–${spent(cost.high)} · `;
}

function tokens(value: number): string {
  return value >= 1000 ? `${Math.round(value / 1000)}k` : String(value);
}

function Receipt({ status }: { status: NonNullable<LatestBuildResponse["honestStatus"]> }) {
  const rows: Array<{ label: string; items: string[]; cls: string; mark: string }> = [
    { label: "Works", items: status.working, cls: "text-verified", mark: "✓" },
    { label: "Needs a look", items: status.needs_look, cls: "text-attention", mark: "!" },
    { label: "Not built", items: status.blocked, cls: "text-muted", mark: "—" },
    { label: "Failed", items: status.failed, cls: "text-danger", mark: "×" },
  ];
  return (
    <div className="bg-surface border border-line rounded-card p-[18px]">
      <div className="font-mono text-[11px] uppercase tracking-[0.14em] text-muted mb-3">
        What's true about this build
      </div>
      {rows
        .filter((row) => row.items.length > 0)
        .map((row) => (
          <div key={row.label} className="py-1.5 border-b border-line last:border-0">
            <div className={`text-[12px] font-medium ${row.cls}`}>
              <span className="font-mono mr-1.5">{row.mark}</span>
              {row.label} ({row.items.length})
            </div>
            <div className="text-[13px] text-muted mt-1">{row.items.join(", ")}</div>
          </div>
        ))}
      {status.remainders.length > 0 && (
        <ul className="mt-3 pt-3 border-t border-line flex flex-col gap-1.5">
          {status.remainders.map((line) => (
            <li key={line} className="text-[13px] text-attention">
              {line}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

export function RevealPage() {
  const { projectId = "" } = useParams();
  const api = useApi();
  const navigate = useNavigate();
  const [build, setBuild] = useState<LatestBuildResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(() => {
    setError(null);
    api
      .latestBuild(projectId)
      .then(setBuild)
      .catch((err) => setError(err instanceof ApiError ? err.message : "Something went wrong"));
  }, [api, projectId]);

  useEffect(load, [load]);

  const status = build?.honestStatus ?? null;
  const works = status?.works ?? false;

  return (
    <section>
      <Eyebrow>Ready</Eyebrow>
      <PageTitle>{works ? "Here's your app" : "Here's your app — with a few notes"}</PageTitle>
      <Lede>
        {status?.summary?.split("\n")[0] ?? "Running from your project's own code, which you own."}
      </Lede>

      {error && (
        <div className="mb-4">
          <StateCard
            icon="!"
            tone="error"
            title="Couldn't load the build"
            action={
              <Button variant="ghost" onClick={load}>
                Retry
              </Button>
            }
          >
            {error}
          </StateCard>
        </div>
      )}

      {status?.standin && (
        <p className="font-mono text-xs text-attention border border-attention/40 rounded-btn px-3 py-2 mb-4">
          Built with the stand-in builder — no API keys are configured, so the pipeline is real but
          the code inside is placeholder.
        </p>
      )}

      <div className="grid grid-cols-[1fr_320px] max-md:grid-cols-1 gap-[18px]">
        <div className="bg-surface border border-line rounded-card overflow-hidden">
          <div className="flex items-center gap-2 px-3 py-2 border-b border-line bg-surface-2">
            <span className="w-2.5 h-2.5 rounded-full bg-line-strong" />
            <span className="w-2.5 h-2.5 rounded-full bg-line-strong" />
            <span className="w-2.5 h-2.5 rounded-full bg-line-strong" />
            <span className="font-mono text-[11px] text-muted ml-2 truncate">
              {build?.previewUrl ?? "no preview"}
            </span>
          </div>
          {build?.previewUrl ? (
            <iframe
              title="Your app"
              src={build.previewUrl}
              className="w-full h-[520px] border-0 bg-white"
            />
          ) : (
            <div className="h-[520px] flex items-center justify-center text-[13px] text-muted">
              {build ? "The preview isn't running right now." : "Loading…"}
            </div>
          )}
        </div>

        <aside className="flex flex-col gap-[18px]">
          {build?.whole && (
            <div className="bg-surface border border-line rounded-card p-[18px] relative">
              <span className="absolute top-3 left-3 w-2.5 h-2.5 border-t-[1.5px] border-l-[1.5px] border-line-strong" />
              <div className="font-mono text-[11px] uppercase tracking-[0.14em] text-muted mb-2.5">
                What you built
              </div>
              <p className="text-[13px] leading-relaxed whitespace-pre-wrap">{build.whole}</p>
            </div>
          )}

          {status && <Receipt status={status} />}

          {build?.buildVersion && (
            <p className="font-mono text-[11px] text-muted" data-testid="build-provenance">
              version {build.buildVersion.number} · {build.buildVersion.gitSha.slice(0, 12)}
              {/* Estimated against actual. The estimate alone is a promise; the
                  spend alone is a number with nothing to judge it by. Shown
                  together, an estimate becomes something you can trust the
                  second time — or knowingly distrust. */}
              {build.spend && (
                <>
                  {" · "}
                  {estimated(build.estimate)}
                  {spent(build.spend.costUsd)} spent
                  {build.spend.tokens > 0 && ` · ${tokens(build.spend.tokens)} tokens`}
                </>
              )}
            </p>
          )}

          <div className="flex flex-col gap-2">
            <Button onClick={() => navigate("/live")}>Open & refine →</Button>
            <Button variant="ghost" onClick={() => navigate("/ship")}>
              Get the code
            </Button>
            <Button variant="ghost" onClick={() => navigate("/ship")}>
              Publish
            </Button>
          </div>
        </aside>
      </div>
    </section>
  );
}
