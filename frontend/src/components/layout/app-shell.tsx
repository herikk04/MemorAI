import * as React from "react";
import { NavLink } from "react-router-dom";
import {
  Brain,
  LayoutDashboard,
  Layers,
  Flame,
  Trophy,
  Users,
  Settings,
  Search,
  BarChart3,
} from "lucide-react";

import { cn } from "@/lib/utils";
import { ThemeToggle } from "@/components/theme/theme-toggle";
import { TooltipProvider } from "@/components/ui/tooltip";
import { tokenService } from "@/lib/token-service";
import { authApi } from "@/api/auth";
import { useNavigate } from "react-router-dom";

/**
 * AppShell — Design System MemorAI §8
 * Sidebar w-60 sticky h-screen / Header h-14 sticky top-0 z-30 blur backdrop /
 * Main px-4 py-6 lg:px-8 lg:py-8.
 *
 * A sidebar usa NavLink do react-router (active state automatico).
 */

interface NavItem {
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  to: string;
  end?: boolean; // match exato (pros NavLink)
  badge?: string;
}

const NAV_MAIN: NavItem[] = [
  { label: "Dashboard", icon: LayoutDashboard, to: "/dashboard", end: true },
  { label: "Revisar hoje", icon: Flame, to: "/review" },
  { label: "Meus decks", icon: Layers, to: "/decks" },
];

const NAV_COMMUNITY: NavItem[] = [
  { label: "Relatório", icon: BarChart3, to: "/report" },
  { label: "Ranking", icon: Trophy, to: "/ranking" },
  { label: "Comunidade", icon: Users, to: "/community" },
];

const NAV_BOTTOM: NavItem[] = [
  { label: "Configurações", icon: Settings, to: "/settings" },
];

export function AppShell({
  children,
  className,
}: {
  children: React.ReactNode;
  className?: string;
}) {
  const user = tokenService.getUser();
  const navigate = useNavigate();

  async function handleLogout() {
    await authApi.logout();
    navigate("/login", { replace: true });
  }

  return (
    <TooltipProvider delayDuration={150}>
      <div className="flex min-h-full bg-background text-foreground">
        {/* ============ Sidebar (§8) ============ */}
        <aside className="sticky top-0 hidden h-screen w-60 shrink-0 flex-col border-r border-sidebar-border bg-sidebar text-sidebar-foreground lg:flex">
          {/* Logo no topo */}
          <NavLink to="/dashboard" className="flex h-14 items-center gap-2 border-b border-sidebar-border px-4 hover:bg-sidebar-accent/50">
            <span className="flex size-8 items-center justify-center rounded-lg bg-primary text-primary-foreground shadow-sm">
              <Brain className="size-5 stroke-2" />
            </span>
            <span className="text-lg font-semibold tracking-tight">
              Memor<span className="text-primary">AI</span>
            </span>
          </NavLink>

          {/* Nav */}
          <nav className="flex flex-1 flex-col gap-6 overflow-y-auto p-3">
            <NavSection items={NAV_MAIN} />
            <NavSection items={NAV_COMMUNITY} />
            <div className="mt-auto">
              <NavSection items={NAV_BOTTOM} />
            </div>
          </nav>

          {/* Usuário */}
          <div className="border-t border-sidebar-border p-3">
            <div className="flex items-center gap-3 rounded-md px-2 py-2">
              <div className="flex size-8 items-center justify-center rounded-full bg-primary text-xs font-semibold text-primary-foreground">
                {(user?.username ?? "?").slice(0, 2).toUpperCase()}
              </div>
              <div className="min-w-0 flex-1">
                <p className="truncate text-sm font-medium">
                  {user?.username ?? "Convidado"}
                </p>
                <button
                  type="button"
                  onClick={handleLogout}
                  className="text-xs text-muted-foreground hover:text-foreground hover:underline"
                >
                  Sair
                </button>
              </div>
            </div>
          </div>
        </aside>

        {/* ============ Conteúdo ============ */}
        <div className="flex min-w-0 flex-1 flex-col">
          {/* Header (§8: h-14 sticky backdrop blur) */}
          <header className="sticky top-0 z-30 flex h-14 items-center justify-between gap-4 border-b bg-background/80 px-4 backdrop-blur lg:px-8">
            <div className="flex items-center gap-2 lg:hidden">
              <NavLink to="/dashboard" className="flex items-center gap-2">
                <span className="flex size-8 items-center justify-center rounded-lg bg-primary text-primary-foreground">
                  <Brain className="size-5 stroke-2" />
                </span>
                <span className="font-semibold tracking-tight">
                  Memor<span className="text-primary">AI</span>
                </span>
              </NavLink>
            </div>

            {/* Busca inline em desktop (§8) — TODO: integrar com /ai/search/ */}
            <div className="hidden flex-1 lg:block">
              <button
                type="button"
                className="flex h-9 w-full max-w-xs items-center gap-2 rounded-md border border-input bg-background px-3 text-sm text-muted-foreground shadow-sm transition-colors hover:bg-accent hover:text-accent-foreground"
              >
                <Search className="size-4 stroke-2" />
                <span>Buscar decks...</span>
                <span className="ml-auto rounded border border-border px-1.5 py-0.5 text-[10px] leading-none">
                  ⌘K
                </span>
              </button>
            </div>

            <div className="flex items-center gap-1">
              <ThemeToggle />
            </div>
          </header>

          {/* Main (§8: px-4 py-6 lg:px-8 lg:py-8) */}
          <main className={cn("flex-1 px-4 py-6 lg:px-8 lg:py-8", className)}>
            {children}
          </main>
        </div>
      </div>
    </TooltipProvider>
  );
}

function NavSection({ items }: { items: NavItem[] }) {
  return (
    <ul className="space-y-0.5">
      {items.map((item) => {
        const Icon = item.icon;
        const isExternal = item.to.startsWith("#");
        return (
          <li key={item.label}>
            {isExternal ? (
              <span className="flex cursor-not-allowed items-center gap-2.5 rounded-md px-2.5 py-1.5 text-sm font-medium text-sidebar-foreground/40">
                <Icon className="size-4 shrink-0 stroke-2 text-muted-foreground" />
                <span className="flex-1 truncate">{item.label}</span>
              </span>
            ) : (
              <NavLink
                to={item.to}
                end={item.end}
                className={({ isActive }) =>
                  cn(
                    "group flex items-center gap-2.5 rounded-md px-2.5 py-1.5 text-sm font-medium transition-colors",
                    isActive
                      ? "bg-sidebar-accent text-sidebar-accent-foreground"
                      : "text-sidebar-foreground/80 hover:bg-sidebar-accent hover:text-sidebar-accent-foreground"
                  )
                }
              >
                {({ isActive }) => (
                  <>
                    <Icon
                      className={cn(
                        "size-4 shrink-0 stroke-2",
                        isActive
                          ? "text-primary"
                          : "text-muted-foreground group-hover:text-sidebar-accent-foreground"
                      )}
                    />
                    <span className="flex-1 truncate">{item.label}</span>
                    {item.badge ? (
                      <span className="rounded-full bg-primary px-1.5 py-0.5 text-[10px] font-semibold leading-none text-primary-foreground">
                        {item.badge}
                      </span>
                    ) : null}
                  </>
                )}
              </NavLink>
            )}
          </li>
        );
      })}
    </ul>
  );
}
