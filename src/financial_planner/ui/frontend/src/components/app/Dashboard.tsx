import { useMemo } from "react";
import { useAppStore } from "@/store/useAppStore";
import { fmtCurrency, fmtVolume, fmtPriceUnit, fmtNumber } from "@/lib/format";
import { Download, Loader2, TrendingDown, TrendingUp, AlertCircle } from "lucide-react";
import { Button } from "@/components/ui/button";

const RESULT_TABS = [
  { key: "revenue", label: "Revenue" },
  { key: "rm_costs", label: "RM Cost" },
  { key: "var_costs", label: "Variable" },
  { key: "dist_costs", label: "Distribution" },
  { key: "vcm", label: "VCM" },
] as const;

function KPI({
  label,
  value,
  sub,
  highlight,
}: {
  label: string;
  value: string;
  sub?: string;
  highlight?: "brand" | "positive" | "negative";
}) {
  return (
    <div className="relative rounded-xl border border-border bg-card p-4 shadow-elevated overflow-hidden">
      {highlight === "brand" && (
        <div className="pointer-events-none absolute inset-0 bg-aurora opacity-70" />
      )}
      <div className="relative">
        <div className="text-[11px] uppercase tracking-[0.14em] text-muted-foreground">{label}</div>
        <div
          className={
            "mt-2 text-[22px] font-semibold tabular tracking-tight " +
            (highlight === "positive" ? "text-positive" : highlight === "negative" ? "text-negative" : "")
          }
        >
          {value}
        </div>
        {sub && <div className="mt-1 text-[11px] text-muted-foreground tabular">{sub}</div>}
      </div>
    </div>
  );
}

export function Dashboard() {
  const {
    selectedScenario,
    selectedScenarioMeta,
    calculatedMetrics: m,
    calculatedPreview,
    currencyMode,
    activeResultsTab,
    setActiveResultsTab,
    loadingCalculation,
    calculationError,
  } = useAppStore();

  const isUSD = currencyMode === "USD";

  const columns = useMemo(() => {
    const base = ["Material", "Material ID", "Plant", "Sold to", "Ship to ID", "Date", "Volume"];
    switch (activeResultsTab) {
      case "revenue":
        return [...base, "Price_USD", "Revenue_USD", "Revenue_LC"];
      case "rm_costs":
        return [...base, "Unit_RM_Cost_USD", "Total_RM_Cost_USD", "Total_RM_Cost_LC"];
      case "var_costs":
        return [...base, "Total_Var_Cost_USD", "Total_Var_Cost_LC"];
      case "dist_costs":
        return [...base, "Total_Dist_Cost_USD", "Total_Dist_Cost_LC"];
      case "vcm":
        return [...base, "VCM_USD", "VCM_LC"];
    }
  }, [activeResultsTab]);

  const numericCols = new Set([
    "Volume",
    "Price_USD",
    "Revenue_USD",
    "Revenue_LC",
    "Unit_RM_Cost_USD",
    "Total_RM_Cost_USD",
    "Total_RM_Cost_LC",
    "Total_Var_Cost_USD",
    "Total_Var_Cost_LC",
    "Total_Dist_Cost_USD",
    "Total_Dist_Cost_LC",
    "VCM_USD",
    "VCM_LC",
  ]);

  const exportUrl = selectedScenario ? `/api/scenarios/${selectedScenario}/export` : "#";

  return (
    <div className="space-y-6">
      {calculationError && (
        <div className="flex items-start gap-2 rounded-lg border border-destructive/40 bg-destructive/10 text-destructive p-3 text-sm">
          <AlertCircle className="size-4 mt-0.5 shrink-0" />
          <div>{calculationError}</div>
        </div>
      )}

      {/* Scenario header */}
      <div className="rounded-2xl border border-border bg-card p-6 relative overflow-hidden shadow-elevated">
        <div className="absolute inset-0 bg-aurora opacity-60 pointer-events-none" />
        <div className="relative flex flex-wrap items-start justify-between gap-4">
          <div>
            <div className="text-[11px] uppercase tracking-[0.14em] text-muted-foreground">Active scenario</div>
            <h2 className="mt-1 text-2xl font-semibold tracking-tight">
              <span className="text-gradient-brand">{selectedScenario ?? "—"}</span>
            </h2>
            <div className="mt-1 text-sm text-muted-foreground">
              {selectedScenarioMeta?.description || "No description provided."}
            </div>
            <div className="mt-3 flex flex-wrap gap-x-5 gap-y-1 text-[12px] text-muted-foreground tabular">
              {selectedScenarioMeta?.created_at && (
                <span>
                  Created <span className="text-foreground">{selectedScenarioMeta.created_at.slice(0, 10)}</span>
                </span>
              )}
              {selectedScenarioMeta?.base_scenario && (
                <span>
                  Base <span className="text-foreground">{selectedScenarioMeta.base_scenario}</span>
                </span>
              )}
              <span>
                Currency <span className="text-foreground">{currencyMode}</span>
              </span>
            </div>
          </div>
          <Button asChild variant="outline" className="gap-2">
            <a href={exportUrl} download>
              <Download className="size-4" /> Export SAC CSV
            </a>
          </Button>
        </div>
      </div>

      {/* KPI Grid */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        <KPI label="Total Volume" value={fmtVolume(m?.total_volume)} highlight="brand" />
        <KPI
          label="Total Revenue"
          value={fmtCurrency(isUSD ? m?.total_revenue_usd : m?.total_revenue_lc, currencyMode)}
          highlight="brand"
        />
        <KPI
          label="Total VCM"
          value={fmtCurrency(isUSD ? m?.total_vcm_usd : m?.total_vcm_lc, currencyMode)}
          highlight={(m?.total_vcm_usd ?? 0) >= 0 ? "positive" : "negative"}
        />
        <KPI
          label="Weighted Avg Price"
          value={fmtPriceUnit(isUSD ? m?.weighted_avg_price_usd : m?.weighted_avg_price_lc, currencyMode)}
          sub="per MT"
        />
        <KPI
          label="Raw Material Cost"
          value={fmtCurrency(isUSD ? m?.total_rm_cost_usd : m?.total_rm_cost_lc, currencyMode)}
        />
        <KPI
          label="Variable Costs"
          value={fmtCurrency(isUSD ? m?.total_var_cost_usd : m?.total_var_cost_lc, currencyMode)}
        />
        <KPI
          label="Distribution Costs"
          value={fmtCurrency(isUSD ? m?.total_dist_cost_usd : m?.total_dist_cost_lc, currencyMode)}
        />
        <KPI
          label="Weighted Avg VCM"
          value={fmtPriceUnit(isUSD ? m?.weighted_avg_vcm_usd : m?.weighted_avg_vcm_lc, currencyMode)}
          sub="per MT"
          highlight={(m?.weighted_avg_vcm_usd ?? 0) >= 0 ? "positive" : "negative"}
        />
      </div>

      {/* Results Table */}
      <div className="rounded-2xl border border-border bg-card shadow-elevated overflow-hidden">
        <div className="flex items-center justify-between px-4 py-3 border-b border-border">
          <div className="flex items-center gap-1 p-0.5 rounded-md bg-secondary">
            {RESULT_TABS.map((t) => (
              <button
                key={t.key}
                onClick={() => setActiveResultsTab(t.key as any)}
                className={
                  "h-8 px-3 text-[12px] font-medium rounded transition-colors cursor-pointer " +
                  (activeResultsTab === t.key
                    ? "bg-card text-foreground shadow-sm"
                    : "text-muted-foreground hover:text-foreground")
                }
              >
                {t.label}
              </button>
            ))}
          </div>
          <div className="text-[11px] uppercase tracking-[0.14em] text-muted-foreground tabular">
            {calculatedPreview.length} rows preview
          </div>
        </div>
        <div className="relative max-h-[560px] overflow-auto">
          {loadingCalculation && (
            <div className="absolute inset-0 z-10 bg-card/70 backdrop-blur-sm grid place-items-center">
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <Loader2 className="size-4 animate-spin" />
                Running simulation pipeline...
              </div>
            </div>
          )}
          <table className="w-full text-[12px]">
            <thead className="sticky top-0 bg-card border-b border-border z-[1]">
              <tr>
                {columns.map((c) => (
                  <th
                    key={c}
                    className={
                      "px-3 py-2.5 text-[11px] font-medium uppercase tracking-[0.1em] text-muted-foreground " +
                      (numericCols.has(c) ? "text-right" : "text-left")
                    }
                  >
                    {c.replace(/_/g, " ")}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {calculatedPreview.length === 0 && !loadingCalculation && (
                <tr>
                  <td colSpan={columns.length} className="text-center text-muted-foreground py-12 text-sm">
                    No results to show. Upload all required files and run a calculation.
                  </td>
                </tr>
              )}
              {calculatedPreview.map((row, i) => (
                <tr key={i} className="border-b border-border/60 hover:bg-secondary/40">
                  {columns.map((c) => {
                    const v = row[c];
                    const isNum = numericCols.has(c);
                    let rendered: string = "—";
                    if (v !== null && v !== undefined && v !== "") {
                      if (isNum) {
                        rendered = c === "Volume" ? fmtNumber(Number(v), 3) : fmtNumber(Number(v), 2);
                      } else {
                        rendered = String(v);
                      }
                    }
                    const negative = isNum && c.includes("VCM") && Number(v) < 0;
                    return (
                      <td
                        key={c}
                        className={
                          "px-3 py-2 " +
                          (isNum ? "text-right tabular font-mono text-[12px] " : "") +
                          (negative ? "text-negative" : "")
                        }
                      >
                        {rendered}
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Change log */}
      {selectedScenarioMeta && selectedScenarioMeta.change_log?.length > 0 && (
        <div className="rounded-2xl border border-border bg-card shadow-elevated">
          <div className="px-4 py-3 border-b border-border flex items-center gap-2">
            <div className="text-[11px] uppercase tracking-[0.14em] text-muted-foreground">Change log</div>
            <span className="text-[11px] text-muted-foreground tabular">
              · {selectedScenarioMeta.change_log.length} entries
            </span>
          </div>
          <ul className="divide-y divide-border max-h-[280px] overflow-auto">
            {selectedScenarioMeta.change_log.map((c, i) => {
              const positive = /increase|added|\+/i.test(c);
              const negative = /decrease|removed|-/i.test(c);
              const Icon = positive ? TrendingUp : negative ? TrendingDown : null;
              return (
                <li key={i} className="px-4 py-2.5 text-[13px] flex items-start gap-2">
                  {Icon && (
                    <Icon
                      className={
                        "size-3.5 mt-0.5 " + (positive ? "text-positive" : negative ? "text-negative" : "")
                      }
                    />
                  )}
                  <span className="text-foreground/90">{c}</span>
                </li>
              );
            })}
          </ul>
        </div>
      )}
    </div>
  );
}
