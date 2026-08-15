import {
  ClerkProvider,
  RedirectToSignIn,
  SignedIn,
  SignedOut,
  SignIn,
  UserButton,
  useAuth,
} from "@clerk/clerk-react";
import { useCallback, useState, type ReactNode } from "react";
import { useNavigate } from "react-router-dom";
import { Button, LogoTile, StateCard } from "../components/ui";

/**
 * Which identity provider the front end runs on — the app's half of ADR-0008.
 *
 * The backend has had a swappable IdentityVerifier since 3.3; the front end had
 * Clerk hard-wired into four files, so nobody could open the product without a
 * Clerk account and two keys. That is why it had never been clicked through.
 *
 * There are two implementations. Clerk is what ships. Dev auth is for local
 * work in this sandbox: it signs you in as an email you type, keeps it in
 * localStorage, and sends `Bearer dev:<email>` — which the api's
 * DevIdentityVerifier accepts, and only when SCIO_DEV_AUTH is set there too.
 * Two emails are two workspaces, so scoping can be checked by hand.
 *
 * The choice is made ONCE, at module load, from a build-time flag. Nothing
 * downstream branches, and no hook is called conditionally.
 */

export const DEV_AUTH = ["1", "true", "yes"].includes(
  String(import.meta.env.VITE_DEV_AUTH ?? "").toLowerCase(),
);

const DEV_STORAGE_KEY = "scio.dev-auth.email";
const DEFAULT_DEV_EMAIL = "dev@scio.local";

interface AuthImpl {
  /** Wraps the whole app. */
  Provider: (props: { children: ReactNode }) => JSX.Element;
  /** Renders children only when signed in; otherwise sends them to sign in. */
  Gate: (props: { children: ReactNode }) => JSX.Element;
  /** The sign-in screen, mounted at /sign-in. */
  SignInScreen: () => JSX.Element;
  /** The avatar/menu in the shell's footer. */
  Badge: () => JSX.Element;
  /** The token the API client attaches per request. */
  useToken: () => () => Promise<string | null>;
}

// --------------------------------------------------------------------------
// Clerk — what ships
// --------------------------------------------------------------------------

const clerkImpl: AuthImpl = {
  Provider: ({ children }) => {
    const publishableKey = import.meta.env.VITE_CLERK_PUBLISHABLE_KEY as string | undefined;
    if (!publishableKey) {
      return (
        <div className="min-h-screen flex items-center justify-center p-6">
          <StateCard icon="⚙" tone="warn" title="Auth isn't configured">
            Set <code className="font-mono">VITE_CLERK_PUBLISHABLE_KEY</code> in{" "}
            <code className="font-mono">apps/app/.env</code> to enable sign-in — or set{" "}
            <code className="font-mono">VITE_DEV_AUTH=1</code> to run locally with dev auth
            (see docs/RUNBOOK-LOCAL.md).
          </StateCard>
        </div>
      );
    }
    return (
      <ClerkProvider publishableKey={publishableKey} afterSignOutUrl="/sign-in">
        {children}
      </ClerkProvider>
    );
  },
  Gate: ({ children }) => (
    <>
      <SignedIn>{children}</SignedIn>
      <SignedOut>
        <RedirectToSignIn />
      </SignedOut>
    </>
  ),
  SignInScreen: () => <SignIn routing="path" path="/sign-in" />,
  Badge: () => <UserButton afterSignOutUrl="/sign-in" />,
  useToken: () => {
    const { getToken } = useAuth();
    // Memoised: useApi keys its client on this, and a fresh function every
    // render would rebuild the client and re-fire every page's load effect.
    return useCallback(() => getToken(), [getToken]);
  },
};

// --------------------------------------------------------------------------
// Dev auth — local only
// --------------------------------------------------------------------------

function devEmail(): string | null {
  try {
    return window.localStorage.getItem(DEV_STORAGE_KEY);
  } catch {
    return null;
  }
}

const devImpl: AuthImpl = {
  Provider: ({ children }) => <>{children}</>,
  Gate: ({ children }) => {
    const navigate = useNavigate();
    if (!devEmail()) {
      // Not a redirect component: this runs inside the router already, and a
      // render-time navigate is what keeps the URL honest.
      queueMicrotask(() => navigate("/sign-in", { replace: true }));
      return <></>;
    }
    return <>{children}</>;
  },
  SignInScreen: () => {
    const navigate = useNavigate();
    const [email, setEmail] = useState(devEmail() ?? DEFAULT_DEV_EMAIL);
    return (
      <div className="w-[380px] bg-surface border border-line rounded-card p-6">
        <div className="flex items-center gap-2.5 mb-4">
          <LogoTile />
          <span className="font-display font-semibold text-[19px]">Scio</span>
        </div>
        <div className="font-mono text-[11px] uppercase tracking-[0.14em] text-attention mb-2">
          Dev auth — local only
        </div>
        <p className="text-[13px] text-muted mb-4">
          No Clerk, no password. Whatever you type becomes a user and a workspace; a different
          email is a different workspace.
        </p>
        <form
          data-testid="dev-sign-in"
          onSubmit={(event) => {
            event.preventDefault();
            window.localStorage.setItem(DEV_STORAGE_KEY, email.trim() || DEFAULT_DEV_EMAIL);
            navigate("/projects", { replace: true });
          }}
        >
          <input
            aria-label="Email"
            className="w-full rounded-btn border border-line bg-paper px-3 py-2 text-sm mb-3"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
          />
          <Button type="submit" className="w-full">
            Continue
          </Button>
        </form>
      </div>
    );
  },
  Badge: () => {
    const navigate = useNavigate();
    return (
      <button
        type="button"
        title={`Signed in as ${devEmail() ?? "nobody"} — click to sign out`}
        onClick={() => {
          window.localStorage.removeItem(DEV_STORAGE_KEY);
          navigate("/sign-in", { replace: true });
        }}
        className="w-7 h-7 rounded-full bg-teal-tint text-teal text-xs font-medium flex-none"
      >
        {(devEmail() ?? "?").slice(0, 1).toUpperCase()}
      </button>
    );
  },
  useToken: () =>
    useCallback(() => Promise.resolve(`dev:${devEmail() ?? DEFAULT_DEV_EMAIL}`), []),
};

const impl: AuthImpl = DEV_AUTH ? devImpl : clerkImpl;

export const AuthProvider = impl.Provider;
export const AuthGate = impl.Gate;
export const SignInScreen = impl.SignInScreen;
export const UserBadge = impl.Badge;
export const useAuthToken = impl.useToken;
