import { useEffect, useState } from "react";
import { NavLink, Outlet, useLocation, useNavigate } from "react-router-dom";
import { UserBadge } from "../lib/auth";
import { currentTheme, setTheme } from "../lib/theme";
import { Button, LogoTile } from "./ui";

const TITLES: Record<string, string> = {
  "/projects": "Projects",
  "/create": "New project",
  "/settings": "Settings",
};

function NavItem({ to, icon, label }: { to: string; icon: JSX.Element; label: string }) {
  return (
    <NavLink
      to={to}
      className={({ isActive }) =>
        `flex items-center gap-[11px] px-2.5 py-[9px] rounded-btn text-sm border border-transparent transition-colors ${
          isActive
            ? "bg-teal-tint text-teal font-medium"
            : "text-muted hover:bg-surface-2 hover:text-ink"
        }`
      }
    >
      <svg className="w-4 h-4 flex-none" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7">
        {icon}
      </svg>
      <span className="max-md:hidden">{label}</span>
    </NavLink>
  );
}

export function AppShell() {
  const location = useLocation();
  const navigate = useNavigate();
  const [theme, setThemeState] = useState(currentTheme());

  useEffect(() => {
    setTheme(theme);
  }, [theme]);

  const title =
    TITLES[location.pathname] ??
    (location.pathname.startsWith("/projects") ? "Projects" : "Scio");

  return (
    <div className="grid grid-cols-[236px_1fr] max-md:grid-cols-[64px_1fr] h-screen">
      <aside className="bg-surface border-r border-line flex flex-col p-4 px-3">
        <div className="flex items-center gap-2.5 px-2 pb-[18px]">
          <LogoTile />
          <span className="font-display font-semibold text-[19px] max-md:hidden">Scio</span>
        </div>
        <nav className="flex flex-col gap-0.5 mt-1.5">
          <NavItem
            to="/projects"
            label="Projects"
            icon={
              <>
                <rect x="3" y="3" width="7" height="7" rx="1" />
                <rect x="14" y="3" width="7" height="7" rx="1" />
                <rect x="3" y="14" width="7" height="7" rx="1" />
                <rect x="14" y="14" width="7" height="7" rx="1" />
              </>
            }
          />
          <NavItem to="/create" label="New project" icon={<path d="M12 5v14M5 12h14" />} />
          <NavItem
            to="/settings"
            label="Settings"
            icon={
              <>
                <circle cx="12" cy="12" r="3" />
                <path d="M12 2v3M12 19v3M2 12h3M19 12h3M5 5l2 2M17 17l2 2M19 5l-2 2M7 17l-2 2" />
              </>
            }
          />
        </nav>
        <div className="mt-auto border-t border-line pt-3 pl-2 flex items-center gap-2.5">
          <UserBadge />
          <div className="text-xs max-md:hidden">
            <b className="block font-medium">Your workspace</b>
            <span className="text-muted">Starter plan</span>
          </div>
        </div>
      </aside>

      <div className="flex flex-col h-screen overflow-hidden">
        <header className="h-[60px] border-b border-line flex items-center justify-between px-7 flex-none bg-paper">
          <div className="font-display font-semibold text-[17px]">{title}</div>
          <div className="flex items-center gap-3">
            <button
              className="bg-surface border border-line rounded-btn px-2.5 py-1.5 cursor-pointer font-mono text-xs text-ink hover:border-line-strong"
              onClick={() => setThemeState(theme === "dark" ? "light" : "dark")}
              aria-label="Toggle dark mode"
            >
              ◐ {theme === "dark" ? "Light" : "Dark"}
            </button>
            <Button onClick={() => navigate("/create")}>+ New project</Button>
          </div>
        </header>
        <main className="flex-1 overflow-y-auto px-7 pt-8 pb-12">
          <div className="max-w-[920px] mx-auto">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  );
}
