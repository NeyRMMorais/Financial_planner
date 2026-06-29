import { useAppStore } from "@/store/useAppStore";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Loader2, ArrowRight, ArrowUpRight, ArrowDownRight, AlertCircle } from "lucide-react";
import { fmtCurrency, fmtNumber, fmtPriceUnit, fmtVolume } from "@/lib/format";

function DeltaCell({ value, format = "num" }: { value: number; format?: "num" | "usd" | "vol" | "price" }) {
  const positive = value > 0;
  const negative = value < 0;
  const arrow = positive ? (
    <ArrowUpRight className="size-3.5" />
  ) : negative ? (
    <ArrowDownRight className="size-3.5" />
  ) : null;
  const color = positive ? "text-positive" : negative ? "text-negative" : "text-muted-foreground";
  const display =
    format === "usd"
      ? fmtCurrency(value, "USD")
      : format === "vol"
        ? fmtVolume(value)
        : format === "price"
          ? fmtPriceUnit(value, "USD")
          : fmtNumber(value, 2);
  return (
    <span className={"inline-flex items-center gap-1 tabular font-mono " + color}>
      {arrow}
      {display}
    </span>
  );
}

function DeltaKPI({
  label,
  abs,
  pct,
  format,
}: {
  label: string;
  abs: number;
  pct?: string;
  format: "usd" | "vol" | "price";
}) {
  const positive = abs > 0;
  const negative = abs < 0;
  const color = positive ? "border-positive/40 bg-positive/5" : negative ? "border-negative/40 bg-negative/5" : "";
  return (
    <div className={"rounded-xl border p-4 shadow-elevated bg-card " + color}>
      <div className="text-[11px] uppercase tracking-[0.14em] text-muted-foreground">{label}</div>
      <div className="mt-2 text-xl font-semibold">
        <DeltaCell value={abs} format={format} />
      </div>
      {pct !== undefined && <div className="mt-1 text-[12px] text-muted-foreground tabular">{pct}</div>}
    </div>
  );
}

export function Compare() {
  const {
    scenarios,
    compareScenarioA,
    compareScenarioB,
    setCompareScenarioA,
    setCompareScenarioB,
    runComparison,
    compareResult: r,
    loadingCompare,
    compareError,
  } = useAppStore();

  return (
    <div className="space-y-6">
      <div className="rounded-2xl border border-border bg-card shadow-elevated p-6 relative overflow-hidden">
        <div className="absolute inset-0 bg-aurora opacity-60 pointer-events-none" />
        <div className="relative space-y-4">
          <div>
            <div className="text-[11px] uppercase tracking-[0.14em] text-muted-foreground">Compare scenarios</div>
            <h2 className="text-xl font-semibold tracking-tight mt-1">
              Variance analysis between two planning runs
            </h2>
          </div>
          <div className="flex flex-wrap items-end gap-3">
            <div className="space-y-1.5 min-w-[200px]">
              <div className="text-[11px] uppercase tracking-wider text-muted-foreground">Scenario A</div>
              <Select value={compareScenarioA} onValueChange={setCompareScenarioA}>
                <SelectTrigger>
                  <SelectValue placeholder="Select A" />
                </SelectTrigger>
                <SelectContent>
                  {scenarios.map((s) => (
                    <SelectItem key={s.name} value={s.name}>
                      {s.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <ArrowRight className="size-4 text-muted-foreground mb-2.5" />
            <div className="space-y-1.5 min-w-[200px]">
              <div className="text-[11px] uppercase tracking-wider text-muted-foreground">Scenario B</div>
              <Select value={compareScenarioB} onValueChange={setCompareScenarioB}>
                <SelectTrigger>
                  <SelectValue placeholder="Select B" />
                </SelectTrigger>
                <SelectContent>
                  {scenarios.map((s) => (
                    <SelectItem key={s.name} value={s.name}>
                      {s.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <Button
              onClick={runComparison}
              disabled={loadingCompare || !compareScenarioA || !compareScenarioB}
              className="bg-gradient-brand text-white shadow-glow"
            >
              {loadingCompare ? <Loader2 className="size-4 animate-spin" /> : null} Run comparison
            </Button>
          </div>
        </div>
      </div>

      {compareError && (
        <div className="flex items-start gap-2 rounded-lg border border-destructive/40 bg-destructive/10 text-destructive p-3 text-sm">
          <AlertCircle className="size-4 mt-0.5 shrink-0" />
          <div>{compareError}</div>
        </div>
      )}

      {r && (
        <>
          <div className="grid grid-cols-2 lg:grid-cols-5 gap-3">
            <DeltaKPI label="Total Volume Δ" abs={r.absolute_diff.total_volume} pct={r.percentage_diff.total_volume} format="vol" />
            <DeltaKPI
              label="Total Revenue Δ"
              abs={r.absolute_diff.total_revenue_usd}
              pct={r.percentage_diff.total_revenue_usd}
              format="usd"
            />
            <DeltaKPI
              label="Total VCM Δ"
              abs={r.absolute_diff.total_vcm_usd}
              pct={r.percentage_diff.total_vcm_usd}
              format="usd"
            />
            <DeltaKPI
              label="Wt. Avg Price Δ"
              abs={r.absolute_diff.weighted_avg_price_usd}
              pct={r.percentage_diff.weighted_avg_price_usd}
              format="price"
            />
            <DeltaKPI
              label="Wt. Avg VCM Δ"
              abs={r.absolute_diff.weighted_avg_vcm_usd}
              pct={r.percentage_diff.weighted_avg_vcm_usd}
              format="price"
            />
          </div>

          <VarianceTable
            title="VCM variance by Plant"
            rows={r.vcm_variance_by_plant.map((p) => ({
              key: p.Plant,
              cells: [
                p.Plant,
                fmtVolume(p.Volume_A),
                fmtVolume(p.Volume_B),
                <DeltaCell value={p["Volume Delta"]} format="vol" />,
                fmtCurrency(p.VCM_USD_A, "USD"),
                fmtCurrency(p.VCM_USD_B, "USD"),
                <DeltaCell value={p["VCM Delta"]} format="usd" />,
              ],
            }))}
            headers={["Plant", "Volume A", "Volume B", "Volume Δ", "VCM A (USD)", "VCM B (USD)", "VCM Δ"]}
          />

          <VarianceTable
            title="VCM variance by Material"
            rows={r.vcm_variance_by_material.map((m) => ({
              key: m["Material ID"],
              cells: [
                <span>
                  <div className="font-medium">{m.Material}</div>
                  <div className="text-[11px] text-muted-foreground font-mono">{m["Material ID"]}</div>
                </span>,
                fmtVolume(m.Volume_A),
                fmtVolume(m.Volume_B),
                <DeltaCell value={m["Volume Delta"]} format="vol" />,
                fmtCurrency(m.VCM_USD_A, "USD"),
                fmtCurrency(m.VCM_USD_B, "USD"),
                <DeltaCell value={m["VCM Delta"]} format="usd" />,
              ],
            }))}
            headers={["Material", "Volume A", "Volume B", "Volume Δ", "VCM A (USD)", "VCM B (USD)", "VCM Δ"]}
          />

          {r.change_log.length > 0 && (
            <div className="rounded-2xl border border-border bg-card shadow-elevated">
              <div className="px-4 py-3 border-b border-border text-[11px] uppercase tracking-[0.14em] text-muted-foreground">
                Input file differences
              </div>
              <ul className="divide-y divide-border max-h-[300px] overflow-auto">
                {r.change_log.map((c, i) => (
                  <li key={i} className="px-4 py-2.5 text-[13px]">
                    {c}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </>
      )}
    </div>
  );
}

function VarianceTable({
  title,
  headers,
  rows,
}: {
  title: string;
  headers: string[];
  rows: { key: string; cells: React.ReactNode[] }[];
}) {
  return (
    <div className="rounded-2xl border border-border bg-card shadow-elevated overflow-hidden">
      <div className="px-4 py-3 border-b border-border text-sm font-semibold">{title}</div>
      <div className="max-h-[420px] overflow-auto">
        <table className="w-full text-[12px]">
          <thead className="sticky top-0 bg-card border-b border-border">
            <tr>
              {headers.map((h, i) => (
                <th
                  key={h}
                  className={
                    "px-3 py-2 text-[11px] uppercase tracking-[0.1em] text-muted-foreground font-medium " +
                    (i === 0 ? "text-left" : "text-right")
                  }
                >
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.length === 0 && (
              <tr>
                <td colSpan={headers.length} className="text-center text-muted-foreground py-8 text-sm">
                  No variance
                </td>
              </tr>
            )}
            {rows.map((r) => (
              <tr key={r.key} className="border-b border-border/60 hover:bg-secondary/40">
                {r.cells.map((c, i) => (
                  <td key={i} className={"px-3 py-2 " + (i === 0 ? "text-left" : "text-right tabular font-mono")}>
                    {c as any}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
