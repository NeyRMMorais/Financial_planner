import { LayoutDashboard, FolderCog, GitCompareArrows } from "lucide-react";
import { cn } from "@/lib/utils";

const APP_ICON_DARK = "/icon-dark.png";
const APP_ICON_LIGHT = "/icon-light.png";

export type ViewKey = "dashboard" | "manager" | "compare";

export function Sidebar({
  view,
  onView,
  collapsed,
  dark,
}: {
  view: ViewKey;
  onView: (v: ViewKey) => void;
  collapsed?: boolean;
  dark?: boolean;
}) {
  const appIcon = dark ? APP_ICON_DARK : APP_ICON_LIGHT;
  const items = [
    { key: "dashboard" as const, label: "Dashboard", icon: LayoutDashboard },
    { key: "manager" as const, label: "Scenario Manager", icon: FolderCog },
    { key: "compare" as const, label: "Compare", icon: GitCompareArrows },
  ];

  return (
    <aside
      className={cn(
        "shrink-0 border-r border-sidebar-border bg-sidebar text-sidebar-foreground flex flex-col",
        collapsed ? "w-[72px]" : "w-[248px]",
      )}
    >
      <div className="h-16 flex items-center gap-3 px-5 border-b border-sidebar-border">
        <div className="size-9 rounded-xl overflow-hidden shadow-glow ring-1 ring-border/50">
          <img src={appIcon} alt="Financial Planner" className="size-full object-cover" />
        </div>
        {!collapsed && (
          <div className="leading-tight">
            <div className="text-[15px] font-semibold tracking-tight">Financial Planner</div>
          </div>
        )}
      </div>

      <nav className="p-3 flex flex-col gap-1">
        {items.map((it) => {
          const active = view === it.key;
          const Icon = it.icon;
          return (
            <button
              key={it.key}
              onClick={() => onView(it.key)}
              className={cn(
                "group relative flex items-center gap-3 rounded-lg px-3 h-10 text-sm transition-colors cursor-pointer",
                active
                  ? "bg-sidebar-accent text-sidebar-accent-foreground font-medium"
                  : "text-muted-foreground hover:bg-sidebar-accent/60 hover:text-sidebar-foreground",
              )}
            >
              {active && (
                <span className="absolute left-0 top-1.5 bottom-1.5 w-[3px] rounded-r bg-gradient-brand" />
              )}
              <Icon className="size-4" />
              {!collapsed && <span>{it.label}</span>}
            </button>
          );
        })}
      </nav>

      {!collapsed && (
        <div className="mt-auto p-4">
          <div className="rounded-xl border border-sidebar-border bg-aurora p-4">
            <div className="text-[11px] uppercase tracking-[0.14em] text-muted-foreground">Pipeline</div>
            <div className="mt-1 text-sm font-medium">Backend at :8000</div>
            <div className="mt-3 flex items-center gap-2 text-[11px] text-muted-foreground">
              <span className="size-1.5 rounded-full bg-positive shadow-[0_0_8px_var(--positive)]" />
              Proxy /api ready
            </div>
          </div>
        </div>
      )}
    </aside>
  );
}
