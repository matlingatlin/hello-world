import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Button, Eyebrow, Lede, PageTitle } from "../components/ui";
import { ApiError } from "../lib/api";
import { useApi } from "../lib/useApi";

function TypeCard({
  title,
  desc,
  icon,
  soon,
  selected,
  onSelect,
}: {
  title: string;
  desc: string;
  icon: JSX.Element;
  soon?: boolean;
  selected?: boolean;
  onSelect?: () => void;
}) {
  return (
    <div
      className={`bg-surface border rounded-card p-5 relative ${
        soon
          ? "opacity-55 cursor-not-allowed border-line"
          : selected
            ? "border-teal shadow-[0_0_0_1px_var(--teal)] cursor-pointer"
            : "border-line hover:border-teal cursor-pointer"
      }`}
      onClick={soon ? undefined : onSelect}
    >
      {soon && (
        <span className="absolute top-3.5 right-3.5 font-mono text-[9.5px] uppercase tracking-[0.08em] text-muted border border-line-strong rounded px-1.5 py-0.5">
          Soon
        </span>
      )}
      <svg
        className={`w-[26px] h-[26px] mb-3 ${soon ? "stroke-muted" : "stroke-teal"}`}
        viewBox="0 0 24 24"
        fill="none"
        strokeWidth="1.6"
      >
        {icon}
      </svg>
      <h3 className="font-display font-medium text-base mb-1">{title}</h3>
      <p className="text-[13px] text-muted">{desc}</p>
    </div>
  );
}

export function CreatePage() {
  const api = useApi();
  const navigate = useNavigate();
  const [name, setName] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function create() {
    const trimmed = name.trim();
    if (!trimmed) {
      setError("Give your project a name first.");
      return;
    }
    setSaving(true);
    setError(null);
    try {
      const created = await api.createProject({ name: trimmed.slice(0, 200), type: "app" });
      // Straight into the wizard: creating a project and describing it are one
      // intent, and bouncing through the project list breaks that.
      navigate(`/projects/${created.project.id}/wizard`);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Something went wrong");
      setSaving(false);
    }
  }

  return (
    <section>
      <Eyebrow>New project</Eyebrow>
      <PageTitle>What do you want to build?</PageTitle>
      <Lede>Name it in a sentence — Scio will take it from there.</Lede>

      <div className="bg-surface border border-line rounded-card p-[18px] relative">
        <span className="absolute top-3 left-3 w-2.5 h-2.5 border-t-[1.5px] border-l-[1.5px] border-line-strong" />
        <textarea
          className="w-full border-none bg-transparent resize-none font-sans text-base text-ink min-h-[64px] p-1.5 focus:outline-none placeholder:text-muted"
          placeholder="e.g. an app where customers book a table and pick a time"
          value={name}
          onChange={(e) => setName(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              void create();
            }
          }}
        />
        <div className="font-mono text-xs text-muted px-1.5 pb-1">
          Ex: "A booking app for my restaurant with email confirmations."
        </div>
        <div className="flex justify-between items-center mt-2">
          <span className="text-[13px] text-danger min-h-[1em]">{error}</span>
          <Button onClick={() => void create()} disabled={saving}>
            {saving ? "Creating…" : "Create project →"}
          </Button>
        </div>
      </div>

      <div className="text-center text-muted text-[13px] my-6">project type</div>

      <div className="grid grid-cols-3 max-sm:grid-cols-1 gap-4">
        <TypeCard
          title="App"
          desc="Interactive product with data, logic, and users."
          selected
          icon={
            <>
              <rect x="4" y="2" width="16" height="20" rx="2" />
              <path d="M9 22v-4h6v4" />
            </>
          }
        />
        <TypeCard
          title="Website"
          desc="Marketing site, landing page, or portfolio."
          soon
          icon={
            <>
              <rect x="2" y="4" width="20" height="16" rx="2" />
              <path d="M2 9h20" />
            </>
          }
        />
        <TypeCard
          title="Automation"
          desc="A workflow that runs on triggers and schedules."
          soon
          icon={<path d="M4 12h4l3 8 4-16 3 8h4" />}
        />
      </div>

      <p className="font-mono text-xs text-muted mt-[18px] text-center">
        MVP builds apps — website and automation are coming later.
      </p>
    </section>
  );
}
