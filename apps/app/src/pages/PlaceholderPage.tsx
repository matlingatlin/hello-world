import { useNavigate } from "react-router-dom";
import { Button } from "../components/ui";

/** Prototype "ph" screen — real screens are ported in step 2 (B022). */
export function PlaceholderPage({ title }: { title: string }) {
  const navigate = useNavigate();
  return (
    <div className="flex flex-col items-center justify-center text-center min-h-[300px] gap-3.5">
      <div className="w-11 h-11 rounded-btn bg-teal text-on-teal font-mono flex items-center justify-center text-xl">
        →
      </div>
      <h1 className="font-display text-[28px] font-semibold tracking-tight">{title}</h1>
      <p className="text-muted text-sm">This screen is being ported from the prototype next.</p>
      <Button variant="ghost" onClick={() => navigate("/projects")}>
        ← Back to projects
      </Button>
    </div>
  );
}
