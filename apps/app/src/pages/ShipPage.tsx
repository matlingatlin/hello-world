import type { LatestBuildResponse } from "@scio/shared";
import { useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { Button, Eyebrow, Lede, PageTitle, StateCard } from "../components/ui";
import { useApi } from "../lib/useApi";
import { useLoadOnce } from "../lib/useLoadOnce";

/**
 * "Get the code" — what the user owns, and what they cannot do with it yet.
 *
 * This screen used to be a placeholder that said it was "being ported from the
 * prototype". That is worse than useless on the one screen whose subject is
 * ownership: the reveal promises you own what was built, and the button that
 * proves it led to an apology.
 *
 * What is true today is here, in full: the build is a real git commit, named,
 * with the history the build made. What is NOT true today is also here —
 * downloading it, pushing it to your own remote, and publishing it are not
 * built, and what they should be is a product decision rather than an
 * oversight (B084, ADR-0018). Saying so costs one sentence; discovering it by
 * clicking costs trust.
 */
export function ShipPage() {
  const { projectId = "" } = useParams();
  const api = useApi();
  const navigate = useNavigate();

  const [build, setBuild] = useState<LatestBuildResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const [loading, setLoading] = useState(true);
  useLoadOnce(projectId, () => {
    api
      .latestBuild(projectId)
      .then(setBuild)
      .catch((err: unknown) =>
        setError(err instanceof Error ? err.message : "That build could not be read."),
      )
      .finally(() => setLoading(false));
  });

  const version = build?.buildVersion;

  return (
    <section>
      <Eyebrow>Your app</Eyebrow>
      <PageTitle>The code is yours</PageTitle>
      <Lede>
        Every build is a real commit in a real git repository — the history starts at your
        first build, not whenever you think to export.
      </Lede>

      {error && (
        <StateCard icon="!" tone="error" title="That build could not be read">
          {error}
        </StateCard>
      )}

      {!error && !loading && !version && (
        <StateCard
          icon="○"
          tone="warn"
          title="Nothing has been built yet"
          action={
            <Button onClick={() => navigate(`/projects/${projectId}/build`)}>
              Build it
            </Button>
          }
        >
          There is no version to hand over until a build has finished.
        </StateCard>
      )}

      {version && (
        <div className="bg-surface border border-line rounded-card p-[18px] mb-4">
          <div className="font-mono text-[11px] uppercase tracking-[0.14em] text-muted mb-3">
            What you own
          </div>
          <dl className="text-[13px] flex flex-col gap-2">
            <div className="flex gap-3">
              <dt className="text-muted w-28 flex-none">Version</dt>
              <dd>{version.number}</dd>
            </div>
            <div className="flex gap-3">
              <dt className="text-muted w-28 flex-none">Commit</dt>
              <dd className="font-mono text-[12px]">{version.gitSha}</dd>
            </div>
            <div className="flex gap-3">
              <dt className="text-muted w-28 flex-none">Built</dt>
              <dd>{new Date(version.createdAt).toLocaleString()}</dd>
            </div>
            {build?.honestStatus && (
              <div className="flex gap-3">
                <dt className="text-muted w-28 flex-none">Status</dt>
                <dd>{build.honestStatus.summary}</dd>
              </div>
            )}
          </dl>
        </div>
      )}

      {/* The honest half. Named individually, because "coming soon" over three
          different things tells the user nothing about which one they need. */}
      <div className="bg-surface-2 border border-line rounded-card p-[18px]">
        <div className="font-mono text-[11px] uppercase tracking-[0.14em] text-muted mb-3">
          Not built yet
        </div>
        <ul className="text-[13px] text-muted flex flex-col gap-2">
          <li>
            <strong className="text-ink">Downloading the repository.</strong> The commit above
            exists on the machine that built it; there is no way to pull it to yours from here.
          </li>
          <li>
            <strong className="text-ink">Pushing to your own remote.</strong> Your GitHub, your
            account, your history.
          </li>
          <li>
            <strong className="text-ink">Publishing it somewhere permanent.</strong> Whose
            hosting, and on what domain, is a decision nobody has made yet.
          </li>
        </ul>
      </div>

      <div className="mt-4 flex gap-2">
        <Button variant="ghost" onClick={() => navigate(`/projects/${projectId}/reveal`)}>
          ← Back to the build
        </Button>
      </div>
    </section>
  );
}
