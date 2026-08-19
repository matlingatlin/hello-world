import { useNavigate, useParams } from "react-router-dom";
import { Eyebrow, Lede, PageTitle } from "../components/ui";

/**
 * The one choice between the spec and the build.
 *
 * Both paths end in the same place — a running app you refine — so this is not
 * a fork in the product, it is a question about how much you want to see before
 * the expensive part happens. Shaping the design first is recommended because a
 * change made against a preview costs one package's regeneration, and the same
 * change made after a full build costs the build.
 */

function Card({
  tag,
  recommended = false,
  title,
  children,
  flow,
  onClick,
}: {
  tag: string;
  recommended?: boolean;
  title: string;
  children: string;
  flow: string;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`text-left bg-surface border rounded-card p-[22px] cursor-pointer transition-colors hover:border-line-strong focus-visible:outline focus-visible:outline-2 focus-visible:outline-teal focus-visible:outline-offset-2 ${
        recommended ? "border-teal" : "border-line"
      }`}
    >
      <span
        className={`inline-block font-mono text-[10px] uppercase tracking-[0.14em] px-2 py-[3px] rounded-full mb-3 ${
          recommended ? "bg-teal text-on-teal" : "bg-surface-2 text-muted"
        }`}
      >
        {tag}
      </span>
      <h3 className="font-display text-lg font-semibold mb-1.5">{title}</h3>
      <p className="text-[13px] text-muted leading-relaxed">{children}</p>
      <div className="font-mono text-[11px] text-muted mt-4 pt-3 border-t border-line">{flow}</div>
    </button>
  );
}

export function InvolvePage() {
  const { projectId = "" } = useParams();
  const navigate = useNavigate();

  return (
    <section>
      <Eyebrow>One choice</Eyebrow>
      <PageTitle>How involved do you want to be?</PageTitle>
      <Lede>
        Shape the design first, or let Scio build straight away. Either way, you refine the running
        app afterwards.
      </Lede>

      <div className="grid grid-cols-2 max-md:grid-cols-1 gap-[18px] max-w-3xl">
        <Card
          tag="Fastest"
          title="Just build it"
          flow="wizard → build"
          onClick={() => navigate(`/projects/${projectId}/build`)}
        >
          Scio designs and builds it for you, then you refine the running app.
        </Card>
        <Card
          tag="Recommended"
          recommended
          title="Shape the design first"
          flow="wizard → design → build"
          onClick={() => navigate(`/projects/${projectId}/design`)}
        >
          Review and mark up a running preview before the build — more control, fewer surprises.
        </Card>
      </div>
    </section>
  );
}
