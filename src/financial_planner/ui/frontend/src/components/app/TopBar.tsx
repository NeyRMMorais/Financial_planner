import { useState } from "react";
import { Moon, Sun, Plus, ChevronDown, Loader2, DollarSign } from "lucide-react";
import { useAppStore } from "@/store/useAppStore";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
  DropdownMenuLabel,
  DropdownMenuSeparator,
} from "@/components/ui/dropdown-menu";
import { Button } from "@/components/ui/button";
import { NewScenarioDialog } from "./NewScenarioDialog";

const APP_ICON_DARK = "/icon-dark.png";
const APP_ICON_LIGHT = "/icon-light.png";

export function TopBar({ title, subtitle, dark, onToggleDark }: { title: string; subtitle?: string; dark?: boolean; onToggleDark?: () => void }) {
  const {
    scenarios,
    selectedScenario,
    selectScenario,
    currencyMode,
    setCurrencyMode,
    loadingCalculation,
    loadingScenarios,
  } = useAppStore();

  const appIcon = dark ? APP_ICON_DARK : APP_ICON_LIGHT;

  const [openNew, setOpenNew] = useState(false);

  return (
    <header className="h-16 border-b border-border bg-surface/70 backdrop-blur-md sticky top-0 z-30">
      <div className="h-full px-6 flex items-center gap-4">
        <div className="size-8 rounded-lg overflow-hidden shadow-glow ring-1 ring-border/50 shrink-0">
          <img src={appIcon} alt="Financial Planner" className="size-full object-cover" />
        </div>
        <div className="min-w-0">
          <h1 className="text-[15px] font-semibold tracking-tight leading-none">{title}</h1>
          {subtitle && <p className="text-[12px] text-muted-foreground mt-1 leading-none">{subtitle}</p>}
        </div>

        <div className="ml-auto flex items-center gap-2">
          {loadingCalculation && (
            <div className="hidden md:flex items-center gap-2 text-[12px] text-muted-foreground mr-2">
              <Loader2 className="size-3.5 animate-spin" />
              Running simulation pipeline...
            </div>
          )}

          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="outline" className="h-9 gap-2 min-w-[200px] justify-between">
                <span className="truncate text-sm">
                  {loadingScenarios ? "Loading…" : selectedScenario || "Select scenario"}
                </span>
                <ChevronDown className="size-3.5 opacity-60" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-[280px]">
              <DropdownMenuLabel className="text-[11px] uppercase tracking-[0.14em] text-muted-foreground">
                Scenarios
              </DropdownMenuLabel>
              <DropdownMenuSeparator />
              {scenarios.length === 0 && (
                <div className="px-2 py-6 text-center text-xs text-muted-foreground">No scenarios yet</div>
              )}
              {scenarios.map((s) => (
                <DropdownMenuItem
                  key={s.name}
                  onClick={() => selectScenario(s.name)}
                  className="flex flex-col items-start gap-0.5 cursor-pointer"
                >
                  <div className="flex items-center gap-2 w-full">
                    <span className="text-sm font-medium">{s.name}</span>
                    {s.name === selectedScenario && (
                      <span className="ml-auto text-[10px] uppercase tracking-wider text-primary">Active</span>
                    )}
                  </div>
                  {s.description && (
                    <span className="text-[11px] text-muted-foreground line-clamp-1">{s.description}</span>
                  )}
                </DropdownMenuItem>
              ))}
              <DropdownMenuSeparator />
              <DropdownMenuItem onClick={() => setOpenNew(true)} className="cursor-pointer">
                <Plus className="size-3.5" /> New scenario
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>

          <div className="flex items-center rounded-md border border-border p-0.5 bg-surface">
            {(["USD", "LC"] as const).map((m) => (
              <button
                key={m}
                onClick={() => setCurrencyMode(m)}
                className={
                  "h-8 px-3 rounded text-xs font-medium tabular transition-colors cursor-pointer " +
                  (currencyMode === m
                    ? "bg-gradient-brand text-white shadow-glow"
                    : "text-muted-foreground hover:text-foreground")
                }
              >
                <span className="inline-flex items-center gap-1.5">
                  <DollarSign className="size-3" />
                  {m}
                </span>
              </button>
            ))}
          </div>

          <Button
            size="icon"
            variant="outline"
            onClick={() => onToggleDark?.()}
            className="size-9"
            aria-label="Toggle theme"
          >
            {dark ? <Sun className="size-4" /> : <Moon className="size-4" />}
          </Button>

          <Button onClick={() => setOpenNew(true)} className="h-9 bg-gradient-brand text-white shadow-glow hover:opacity-90">
            <Plus className="size-4" /> New scenario
          </Button>
        </div>
      </div>
      <NewScenarioDialog open={openNew} onOpenChange={setOpenNew} />
    </header>
  );
}
