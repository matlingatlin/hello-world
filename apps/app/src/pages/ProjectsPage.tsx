import type { Project } from "@scio/shared";
import { useCallback, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Button, Eyebrow, Lede, PageTitle, StateCard, StatusChip } from "../components/ui";
import { ApiError } from "../lib/api";
import { useApi } from "../lib/useApi";

function relativeTime(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime();
  const mins = Math.floor(diff / 60_000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins}m ago`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours}h ago`;
  return `${Math.floor(hours / 24)}d ago`;
}

function Thumb() {
  return (
    <div className="h-[110px] bg-surface-2 border-b border-line p-4 drafting">
      <div className="h-3.5 w-[46%] bg-line-strong rounded-[3px] my-[9px]" />
      <div className="h-[9px] w-[80%] bg-line rounded-[3px] my-[9px]" />
      <div className="h-[9px] bg-line rounded-[3px] my-[9px]" />
      <div className="h-5 w-[32%] bg-teal opacity-50 rounded my-[9px]" />
    </div>
  );
}

function SkeletonCard() {
  return (
    <div className="bg-surface border border-line rounded-card overflow-hidden animate-pulse">
      <div className="h-[110px] bg-surface-2 border-b border-line" />
      <div className="p-4">
        <div className="h-4 w-1/2 bg-line rounded-[3px]" />
        <div className="h-3 w-1/3 bg-line rounded-[3px] mt-3" />
      </div>
    </div>
  );
}

/**
 * Where opening a project puts you: back where you left off.
 *
 * The status is the only thing the list knows, and it is enough — each value
 * names the gate the project is waiting at. Sending everyone to the wizard
 * would make a finished app ask its owner to describe it again.
 */
function resumeAt(project: { id: string; status: string }): string {
  const at = `/projects/${project.id}`;
  switch (project.status) {
    case "draft":
      return `${at}/wizard`;
    case "spec_locked":
      return `${at}/involve`;
    case "building":
      return `${at}/build`;
    default:
      // ready, error, and anything a later phase adds: the reveal reads the
      // build back and says honestly when there is not one yet.
      return `${at}/reveal`;
  }
}

export function ProjectsPage() {
  const api = useApi();
  const navigate = useNavigate();
  const [projects, setProjects] = useState<Project[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(() => {
    setError(null);
    setProjects(null);
    api
      .listProjects()
      .then((res) => setProjects(res.projects))
      .catch((err) => setError(err instanceof ApiError ? err.message : "Something went wrong"));
  }, [api]);

  useEffect(load, [load]);

  return (
    <section>
      <Eyebrow>Workspace</Eyebrow>
      <PageTitle>Projects</PageTitle>
      <Lede>
        {projects
          ? `${projects.length} project${projects.length === 1 ? "" : "s"} · everything you build here is yours to export.`
          : "Everything you build here is yours to export."}
      </Lede>

      {error && (
        <StateCard
          icon="!"
          tone="error"
          title="Couldn't load your projects"
          action={<Button variant="ghost" onClick={load}>Retry</Button>}
        >
          {error}
        </StateCard>
      )}

      {!error && projects === null && (
        <div className="grid grid-cols-[repeat(auto-fill,minmax(240px,1fr))] gap-[18px] mt-2">
          <SkeletonCard />
          <SkeletonCard />
          <SkeletonCard />
        </div>
      )}

      {!error && projects !== null && projects.length === 0 && (
        <StateCard
          icon="+"
          title="Nothing here yet"
          action={<Button onClick={() => navigate("/create")}>New project</Button>}
        >
          No projects. Describe your first app and Scio takes it from there.
        </StateCard>
      )}

      {!error && projects !== null && projects.length > 0 && (
        <div className="grid grid-cols-[repeat(auto-fill,minmax(240px,1fr))] gap-[18px] mt-2">
          <button
            className="border border-dashed border-line-strong rounded-card bg-transparent flex flex-col items-center justify-center gap-2.5 min-h-[180px] text-muted hover:text-teal hover:border-teal cursor-pointer"
            onClick={() => navigate("/create")}
          >
            <span className="w-[34px] h-[34px] rounded-btn border-[1.5px] border-current flex items-center justify-center text-xl">
              +
            </span>
            New project
          </button>
          {projects.map((p) => (
            // A button, not a div: it says `cursor-pointer` and it is the only
            // way back into a project, so it has to be clickable AND reachable
            // from a keyboard. It was neither — the card was decorated to look
            // like it opened something and did nothing at all, which meant a
            // person who left a project could not get back to it.
            <button
              key={p.id}
              type="button"
              aria-label={`Open ${p.name}`}
              onClick={() => navigate(resumeAt(p))}
              className="text-left bg-surface border border-line rounded-card overflow-hidden cursor-pointer hover:border-line-strong focus-visible:border-teal"
            >
              <Thumb />
              <div className="px-4 py-3.5">
                <h3 className="font-display font-medium text-base">{p.name}</h3>
                <div className="flex items-center justify-between mt-2.5">
                  <StatusChip status={p.status} />
                  <span className="font-mono text-[11px] text-muted">
                    edited {relativeTime(p.updatedAt)}
                  </span>
                </div>
              </div>
            </button>
          ))}
        </div>
      )}
    </section>
  );
}
