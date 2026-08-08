import { ClerkProvider } from "@clerk/clerk-react";
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import { App } from "./App";
import { StateCard } from "./components/ui";
import { initTheme } from "./lib/theme";
import "./styles.css";

initTheme();

const publishableKey = import.meta.env.VITE_CLERK_PUBLISHABLE_KEY as string | undefined;

/** Graceful degradation when auth isn't configured (no key committed, ADR-0008). */
function MissingConfig() {
  return (
    <div className="min-h-screen flex items-center justify-center p-6">
      <StateCard icon="⚙" tone="warn" title="Auth isn't configured">
        Set <code className="font-mono">VITE_CLERK_PUBLISHABLE_KEY</code> in{" "}
        <code className="font-mono">apps/app/.env</code> (see .env.example) to enable
        sign-in. Get keys from the Clerk dashboard.
      </StateCard>
    </div>
  );
}

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    {publishableKey ? (
      <ClerkProvider publishableKey={publishableKey} afterSignOutUrl="/sign-in">
        <BrowserRouter>
          <App />
        </BrowserRouter>
      </ClerkProvider>
    ) : (
      <MissingConfig />
    )}
  </StrictMode>,
);
