import { Navigate, Route, Routes } from "react-router-dom";
import { AppShell } from "./components/AppShell";
import { ErrorBoundary } from "./components/ErrorBoundary";
import { AuthGate, SignInScreen } from "./lib/auth";
import { CreatePage } from "./pages/CreatePage";
import { DesignPage } from "./pages/DesignPage";
import { InvolvePage } from "./pages/InvolvePage";
import { PlaceholderPage } from "./pages/PlaceholderPage";
import { ShipPage } from "./pages/ShipPage";
import { BuildPage } from "./pages/BuildPage";
import { ProjectsPage } from "./pages/ProjectsPage";
import { RevealPage } from "./pages/RevealPage";
import { SpecPage } from "./pages/SpecPage";
import { WizardPage } from "./pages/WizardPage";

const PLACEHOLDERS: Array<{ path: string; title: string }> = [
  { path: "/live", title: "Refine" },
  { path: "/versions", title: "Versions" },
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
            <SignInScreen />
          </div>
        }
      />
      <Route
        element={
          <AuthGate>
            <ErrorBoundary>
              <AppShell />
            </ErrorBoundary>
          </AuthGate>
        }
      >
        <Route path="/" element={<Navigate to="/projects" replace />} />
        <Route path="/projects" element={<ProjectsPage />} />
        <Route path="/create" element={<CreatePage />} />
        {/* Gate 1 is always about one project: the conversation, spec and
            provenance all belong to it, so the routes carry its id. */}
        <Route path="/projects/:projectId/wizard" element={<WizardPage />} />
        <Route path="/projects/:projectId/spec" element={<SpecPage />} />
        <Route path="/projects/:projectId/involve" element={<InvolvePage />} />
        <Route path="/projects/:projectId/design" element={<DesignPage />} />
        <Route path="/projects/:projectId/build" element={<BuildPage />} />
        <Route path="/projects/:projectId/reveal" element={<RevealPage />} />
        <Route path="/projects/:projectId/ship" element={<ShipPage />} />
        <Route path="/wizard" element={<Navigate to="/projects" replace />} />
        <Route path="/spec" element={<Navigate to="/projects" replace />} />
        <Route path="/involve" element={<Navigate to="/projects" replace />} />
        <Route path="/design" element={<Navigate to="/projects" replace />} />
        <Route path="/build" element={<Navigate to="/projects" replace />} />
        <Route path="/reveal" element={<Navigate to="/projects" replace />} />
        <Route path="/ship" element={<Navigate to="/projects" replace />} />
        {PLACEHOLDERS.map(({ path, title }) => (
          <Route key={path} path={path} element={<PlaceholderPage title={title} />} />
        ))}
        <Route path="*" element={<PlaceholderPage title="Not found" />} />
      </Route>
    </Routes>
  );
}
