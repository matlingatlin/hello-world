import { RedirectToSignIn, SignedIn, SignedOut, SignIn } from "@clerk/clerk-react";
import { Navigate, Route, Routes } from "react-router-dom";
import { AppShell } from "./components/AppShell";
import { CreatePage } from "./pages/CreatePage";
import { PlaceholderPage } from "./pages/PlaceholderPage";
import { ProjectsPage } from "./pages/ProjectsPage";
import { SpecPage } from "./pages/SpecPage";
import { WizardPage } from "./pages/WizardPage";

const PLACEHOLDERS: Array<{ path: string; title: string }> = [
  { path: "/involve", title: "How involved" },
  { path: "/design", title: "Design" },
  { path: "/build", title: "Building" },
  { path: "/reveal", title: "Ready" },
  { path: "/live", title: "Refine" },
  { path: "/versions", title: "Versions" },
  { path: "/ship", title: "Ship" },
  { path: "/settings", title: "Settings" },
  { path: "/states", title: "Error & empty states" },
  { path: "/notifications", title: "Notifications" },
];

export function App() {
  return (
    <Routes>
      <Route
        path="/sign-in/*"
        element={
          <div className="min-h-screen flex items-center justify-center">
            <SignIn routing="path" path="/sign-in" />
          </div>
        }
      />
      <Route
        element={
          <>
            <SignedIn>
              <AppShell />
            </SignedIn>
            <SignedOut>
              <RedirectToSignIn />
            </SignedOut>
          </>
        }
      >
        <Route path="/" element={<Navigate to="/projects" replace />} />
        <Route path="/projects" element={<ProjectsPage />} />
        <Route path="/create" element={<CreatePage />} />
        {/* Gate 1 is always about one project: the conversation, spec and
            provenance all belong to it, so the routes carry its id. */}
        <Route path="/projects/:projectId/wizard" element={<WizardPage />} />
        <Route path="/projects/:projectId/spec" element={<SpecPage />} />
        <Route path="/wizard" element={<Navigate to="/projects" replace />} />
        <Route path="/spec" element={<Navigate to="/projects" replace />} />
        {PLACEHOLDERS.map(({ path, title }) => (
          <Route key={path} path={path} element={<PlaceholderPage title={title} />} />
        ))}
        <Route path="*" element={<PlaceholderPage title="Not found" />} />
      </Route>
    </Routes>
  );
}
