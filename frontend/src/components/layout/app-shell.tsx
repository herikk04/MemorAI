import * as React from "react";
import {
  Brain,
  LayoutDashboard,
  Layers,
  Flame,
  Trophy,
  Users,
  Settings,
} from "lucide-react";

import { cn } from "@/lib/utils";
import { ThemeToggle } from "@/components/theme/theme-toggle";
import { TooltipProvider } from "@/components/ui/tooltip";

interface NavItem {
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  href: string;
  badge?: string;
  active?: boolean;
}

const NAV_MAIN: NavItem[] = [
  { label: "Dashboard", icon: LayoutDashboard, href: "#", active: true },
  { label: "Revisar hoje", icon: Flame, href: "#", badge: "24" },
  { label: "Meus decks", icon: Layers, href: "#" },
];

const NAV_COMMUNITY: NavItem[] = [
  { label: "Ranking", icon: Trophy, href: "#" },
  { label: "Comunidade", icon: Users, href: "#" },
];

const NAV_BOTTOM: NavItem[] = [{ label: "Configurações", icon: Settings, href: "#" }];

export function AppShell({
  children,
  className,
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <TooltipProvider delayDuration={150}>
      <div className="flex min-h-full bg-background text-foreground">
        {/* ============ Sidebar ============ */}
        <aside className="sticky top-0 hidden h-screen w-60 shrink-0 flex-col border-r border-sidebar-border bg-sidebar text-sidebar-foreground lg:flex">
          <div className="flex h-14 items-center gap-2 border-b border-sidebar-border px-4">
            <span className="flex size-8 items-center justify-center rounded-lg bg-primary text-primary-foreground shadow-sm">
              <Brain className="size-5" />
            </span>
            <span className="text-lg font-semibold tracking-tight">
              Memor<span className="text-primary">AI</span>
            </span>
          </div>

          <nav className="flex flex-1 flex-col gap-6 overflow-y-auto p-3">
            <NavSection items={NAV_MAIN} />
            <NavSection items={NAV_COMMUNITY} />
            <div className="mt-auto">
              <NavSection items={NAV_BOTTOM} />
            </div>
          </nav>

          <div className="border-t border-sidebar-border p-3">
            <div className="flex items-center gap-3 rounded-md px-2 py-2 hover:bg-sidebar-accent">
              <div className="flex size-8 items-center justify-center rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 text-xs font-semibold text-white">
                MR
              </div>
              <div className="min-w-0 flex-1">
                <p className="truncate text-sm font-medium">Membro</p>
                <p className="truncate text-xs text-muted-foreground">
                  Plano free
                </p>
              </div>
            </div>
          </div>
        </aside>

        {/* ============ Conteúdo ============ */}
        <div className="flex min-w-0 flex-1 flex-col">
          <header className="sticky top-0 z-30 flex h-14 items-center justify-between border-b bg-background/80 px-4 backdrop-blur supports-[backdrop-filter]:bg-background/80 lg:px-8">
            <div className="flex items-center gap-3 lg:hidden">
              <span className="flex size-8 items-center justify-center rounded-lg bg-primary text-primary-foreground">
                <Brain className="size-5" />
              </span>
              <span className="font-semibold tracking-tight">
                Memor<span className="text-primary">AI</span>
              </span>
            </div>
            <div className="hidden lg:block" />
            <div className="flex items-center gap-1">
              <button
                type="button"
                className="flex h-9 items-center gap-2 rounded-md border border-input bg-background px-3 text-sm text-muted-foreground shadow-sm transition-colors hover:bg-accent hover:text-accent-foreground"
              >
                <span className="text-xs">⌘K</span>
                <span>Buscar decks...</span>
              </button>
              <ThemeToggle />
            </div>
          </header>

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
        return (
          <li key={item.label}>
            <a
              href={item.href}
              className={cn(
                "group flex items-center gap-2.5 rounded-md px-2.5 py-1.5 text-sm font-medium transition-colors",
                item.active
                  ? "bg-sidebar-accent text-sidebar-accent-foreground"
                  : "text-sidebar-foreground/80 hover:bg-sidebar-accent/60 hover:text-sidebar-accent-foreground"
              )}
            >
              <Icon
                className={cn(
                  "size-4 shrink-0",
                  item.active
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
            </a>
          </li>
        );
      })}
    </ul>
  );
}
