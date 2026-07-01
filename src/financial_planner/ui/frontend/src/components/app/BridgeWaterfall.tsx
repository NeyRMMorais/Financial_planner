import { useMemo, useState, useEffect, useRef } from "react";
import { useAppStore, BridgeResult } from "@/store/useAppStore";
import { fmtCurrency, fmtVolume } from "@/lib/format";
import { ArrowUpRight, ArrowDownRight, ChevronDown, Search, Presentation, Loader2 } from "lucide-react";

interface BridgeWaterfallProps {
  data: BridgeResult;
}

// Custom MultiSelect Dropdown Component with search and "Select All" checkbox
interface MultiSelectProps {
  label: string;
  options: { id: string; name: string }[];
  selected: string[];
  onChange: (selected: string[]) => void;
}

function MultiSelect({ label, options, selected, onChange }: MultiSelectProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [search, setSearch] = useState("");
  const containerRef = useRef<HTMLDivElement>(null);

  // Close when clicking outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  // Filter options by search text
  const filteredOptions = useMemo(() => {
    return options.filter((opt) =>
      opt.name.toLowerCase().includes(search.toLowerCase()) ||
      opt.id.toLowerCase().includes(search.toLowerCase())
    );
  }, [options, search]);

  const allSelected = options.length > 0 && selected.length === options.length;
  const noneSelected = selected.length === 0;

  const handleSelectAll = () => {
    if (allSelected) {
      onChange([]);
    } else {
      onChange(options.map((o) => o.id));
    }
  };

  const handleToggle = (id: string) => {
    if (selected.includes(id)) {
      onChange(selected.filter((s) => s !== id));
    } else {
      onChange([...selected, id]);
    }
  };

  const buttonText = useMemo(() => {
    if (allSelected) return `All ${label}s`;
    if (noneSelected) return `No ${label}s selected`;
    if (selected.length === 1) {
      const found = options.find((o) => o.id === selected[0]);
      return found ? found.name : selected[0];
    }
    return `${selected.length} ${label}s`;
  }, [selected, options, allSelected, noneSelected, label]);

  return (
    <div className="relative inline-block text-left" ref={containerRef}>
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="h-8 px-2.5 rounded-md border border-border bg-secondary hover:bg-secondary/80 text-[12px] font-medium text-foreground outline-none focus:border-primary transition-all flex items-center justify-between gap-1.5 cursor-pointer min-w-[150px] max-w-[200px]"
      >
        <span className="truncate">{buttonText}</span>
        <ChevronDown className="size-3.5 shrink-0 text-muted-foreground" />
      </button>

      {isOpen && (
        <div className="absolute right-0 mt-1 w-64 rounded-xl border border-border bg-card p-2 shadow-elevated z-50 space-y-2">
          {/* Search box */}
          <div className="relative flex items-center">
            <Search className="absolute left-2 size-3.5 text-muted-foreground" />
            <input
              type="text"
              placeholder={`Search ${label.toLowerCase()}s...`}
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full h-7 pl-7 pr-2 rounded-md border border-border bg-secondary text-[11px] text-foreground outline-none focus:border-primary"
            />
          </div>

          <div className="max-h-48 overflow-y-auto divide-y divide-border/40 select-none">
            {/* Select All checkbox */}
            <div className="py-1">
              <label className="flex items-center gap-2 px-2 py-1.5 hover:bg-secondary/60 rounded-md cursor-pointer text-[12px]">
                <input
                  type="checkbox"
                  checked={allSelected}
                  onChange={handleSelectAll}
                  className="rounded border-border text-primary outline-none accent-primary size-3.5 cursor-pointer"
                />
                <span className="font-semibold">Select All</span>
              </label>
            </div>

            {/* Options list */}
            <div className="py-1 space-y-0.5">
              {filteredOptions.length === 0 ? (
                <div className="text-center py-2 text-[11px] text-muted-foreground">No matches found</div>
              ) : (
                filteredOptions.map((opt) => {
                  const isChecked = selected.includes(opt.id);
                  return (
                    <label
                      key={opt.id}
                      className="flex items-center gap-2 px-2 py-1 hover:bg-secondary/60 rounded-md cursor-pointer text-[12px]"
                    >
                      <input
                        type="checkbox"
                        checked={isChecked}
                        onChange={() => handleToggle(opt.id)}
                        className="rounded border-border text-primary outline-none accent-primary size-3.5 cursor-pointer"
                      />
                      <span className="truncate flex-1">{opt.name}</span>
                    </label>
                  );
                })
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export function BridgeWaterfall({ data }: BridgeWaterfallProps) {
  const { activeCompareScenarioA, activeCompareScenarioB, exportBridgePPTX } = useAppStore();
  const [activeTab, setActiveTab] = useState<"material" | "month">("material");
  const [selectedMaterials, setSelectedMaterials] = useState<string[]>([]);
  const [selectedRegions, setSelectedRegions] = useState<string[]>([]);
  const [exporting, setExporting] = useState(false);

  const handleExportPPTX = async () => {
    setExporting(true);
    try {
      const matFilterText = selectedMaterials.length === materials.length 
        ? "All Materials" 
        : selectedMaterials.length === 0 
          ? "None" 
          : `${selectedMaterials.length} Selected`;

      const regFilterText = selectedRegions.length === regions.length 
        ? "All Regions" 
        : selectedRegions.length === 0 
          ? "None" 
          : selectedRegions.join(", ");

      await exportBridgePPTX({
        scenario_a: activeCompareScenarioA || "Base VCM",
        scenario_b: activeCompareScenarioB || "Target VCM",
        vcm_usd_a: Number(summary.vcm_usd_a),
        volume_effect: Number(summary.volume_effect),
        price_effect: Number(summary.price_effect),
        cost_effect: Number(summary.cost_effect),
        fx_effect: Number(summary.fx_effect),
        vcm_usd_b: Number(summary.vcm_usd_b),
        material_filter: matFilterText,
        region_filter: regFilterText
      });
    } catch (err) {
      console.error(err);
      alert("Failed to export PowerPoint slide");
    } finally {
      setExporting(false);
    }
  };

  const rawPreview = data.raw_preview || [];

  // Extract unique materials
  const materials = useMemo(() => {
    const map = new Map<string, string>();
    rawPreview.forEach((row) => {
      const id = row["Material ID"];
      const name = row["Material"];
      if (id && name) {
        map.set(id, name);
      }
    });
    return Array.from(map.entries())
      .map(([id, name]) => ({ id, name }))
      .sort((a, b) => a.name.localeCompare(b.name));
  }, [rawPreview]);

  // Extract unique regions (last part of Ship to ID country suffix)
  const regions = useMemo(() => {
    const set = new Set<string>();
    rawPreview.forEach((row) => {
      const shipToId = row["Ship to ID"];
      if (shipToId) {
        const parts = shipToId.split("-");
        const region = parts[parts.length - 1];
        if (region) set.add(region);
      }
    });
    return Array.from(set).sort();
  }, [rawPreview]);

  // Initialize selections to select all on options load
  useEffect(() => {
    if (materials.length > 0) {
      setSelectedMaterials(materials.map((m) => m.id));
    }
  }, [materials]);

  useEffect(() => {
    if (regions.length > 0) {
      setSelectedRegions(regions);
    }
  }, [regions]);

  // Filter rows based on multiple selections
  const filteredRows = useMemo(() => {
    return rawPreview.filter((row) => {
      const matMatch = selectedMaterials.includes(row["Material ID"]);
      const shipToId = row["Ship to ID"] || "";
      const rowRegion = shipToId.split("-").pop() || "";
      const regMatch = selectedRegions.includes(rowRegion);
      return matMatch && regMatch;
    });
  }, [rawPreview, selectedMaterials, selectedRegions]);

  // Re-calculate summary metrics based on filtered records
  const summary = useMemo(() => {
    let vcm_usd_a = 0;
    let volume_effect = 0;
    let price_effect = 0;
    let cost_effect = 0;
    let fx_effect = 0;
    let vcm_usd_b = 0;

    filteredRows.forEach((row) => {
      vcm_usd_a += Number(row.VCM_USD_A) || 0;
      volume_effect += Number(row.Volume_Effect) || 0;
      price_effect += Number(row.Price_Effect) || 0;
      cost_effect += Number(row.Cost_Effect) || 0;
      fx_effect += Number(row.FX_Effect) || 0;
      vcm_usd_b += Number(row.VCM_USD_B) || 0;
    });

    return {
      vcm_usd_a,
      volume_effect,
      price_effect,
      cost_effect,
      fx_effect,
      vcm_usd_b,
    };
  }, [filteredRows]);

  // Re-group by Material
  const by_material = useMemo(() => {
    const groups: Record<string, any> = {};
    filteredRows.forEach((row) => {
      const id = row["Material ID"];
      const name = row["Material"] || "";
      const key = `${id}::${name}`;
      if (!groups[key]) {
        groups[key] = {
          Material: name,
          "Material ID": id,
          Vol_A: 0,
          Vol_B: 0,
          VCM_USD_A: 0,
          VCM_USD_B: 0,
          Volume_Effect: 0,
          Price_Effect: 0,
          Cost_Effect: 0,
          FX_Effect: 0,
        };
      }
      groups[key].Vol_A += Number(row.Vol_A) || 0;
      groups[key].Vol_B += Number(row.Vol_B) || 0;
      groups[key].VCM_USD_A += Number(row.VCM_USD_A) || 0;
      groups[key].VCM_USD_B += Number(row.VCM_USD_B) || 0;
      groups[key].Volume_Effect += Number(row.Volume_Effect) || 0;
      groups[key].Price_Effect += Number(row.Price_Effect) || 0;
      groups[key].Cost_Effect += Number(row.Cost_Effect) || 0;
      groups[key].FX_Effect += Number(row.FX_Effect) || 0;
    });

    return Object.values(groups).sort((a: any, b: any) => {
      const diffA = Math.abs(a.VCM_USD_B - a.VCM_USD_A);
      const diffB = Math.abs(b.VCM_USD_B - b.VCM_USD_A);
      return diffB - diffA;
    });
  }, [filteredRows]);

  // Re-group by Month
  const by_month = useMemo(() => {
    const groups: Record<string, any> = {};
    filteredRows.forEach((row) => {
      const date = row["Date"];
      if (!groups[date]) {
        groups[date] = {
          Date: date,
          Vol_A: 0,
          Vol_B: 0,
          VCM_USD_A: 0,
          VCM_USD_B: 0,
          Volume_Effect: 0,
          Price_Effect: 0,
          Cost_Effect: 0,
          FX_Effect: 0,
        };
      }
      groups[date].Vol_A += Number(row.Vol_A) || 0;
      groups[date].Vol_B += Number(row.Vol_B) || 0;
      groups[date].VCM_USD_A += Number(row.VCM_USD_A) || 0;
      groups[date].VCM_USD_B += Number(row.VCM_USD_B) || 0;
      groups[date].Volume_Effect += Number(row.Volume_Effect) || 0;
      groups[date].Price_Effect += Number(row.Price_Effect) || 0;
      groups[date].Cost_Effect += Number(row.Cost_Effect) || 0;
      groups[date].FX_Effect += Number(row.FX_Effect) || 0;
    });

    return Object.values(groups).sort((a: any, b: any) => {
      return String(a.Date).localeCompare(String(b.Date));
    });
  }, [filteredRows]);

  // Prepare steps for waterfall chart
  const waterfallSteps = useMemo(() => {
    const s = summary;
    const base = Number(s.vcm_usd_a);
    const vol = Number(s.volume_effect);
    const price = Number(s.price_effect);
    const cost = Number(s.cost_effect);
    const fx = Number(s.fx_effect);
    const target = Number(s.vcm_usd_b);

    const step1 = base;
    const step2 = step1 + vol;
    const step3 = step2 + price;
    const step4 = step3 + cost;
    const step5 = step4 + fx;

    return [
      { label: activeCompareScenarioA || "Base VCM", start: 0, end: base, change: base, type: "base" as const },
      { label: "Volume Effect", start: step1, end: step2, change: vol, type: "var" as const },
      { label: "Price Effect", start: step2, end: step3, change: price, type: "var" as const },
      { label: "Cost Effect", start: step3, end: step4, change: cost, type: "var" as const },
      { label: "FX Effect", start: step4, end: step5, change: fx, type: "var" as const },
      { label: activeCompareScenarioB || "Target VCM", start: 0, end: target, change: target, type: "target" as const },
    ];
  }, [summary, activeCompareScenarioA, activeCompareScenarioB]);

  // Find min/max values for scaling the SVG chart
  const scale = useMemo(() => {
    const base = Number(summary.vcm_usd_a);
    const vol = Number(summary.volume_effect);
    const price = Number(summary.price_effect);
    const cost = Number(summary.cost_effect);
    const target = Number(summary.vcm_usd_b);

    const runningValues = [
      0,
      base,
      base + vol,
      base + vol + price,
      base + vol + price + cost,
      target,
    ];
    const absoluteMin = Math.min(...runningValues);
    const absoluteMax = Math.max(...runningValues);

    const range = absoluteMax - absoluteMin;
    const padding = range * 0.15 || 1000;

    return {
      min: absoluteMin - padding,
      max: absoluteMax + padding,
    };
  }, [summary]);

  const chartHeight = 280;
  const getY = (val: number) => {
    const min = scale.min;
    const max = scale.max;
    return chartHeight - ((val - min) / (max - min)) * chartHeight;
  };

  const getBarColor = (step: typeof waterfallSteps[0]) => {
    if (step.type === "base" || step.type === "target") {
      return "var(--primary)";
    }
    if (step.change > 0) {
      return "var(--positive)";
    }
    if (step.change < 0) {
      return "var(--negative)";
    }
    return "var(--muted-foreground)";
  };

  return (
    <div className="space-y-6">
      {/* Waterfall Visualizer */}
      <div className="rounded-2xl border border-border bg-card p-6 shadow-elevated space-y-4">
        {/* Header containing Title and Filters */}
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <div className="text-[11px] uppercase tracking-[0.14em] text-muted-foreground">VCM Waterfall Bridge</div>
            <h3 className="text-lg font-semibold mt-1">Scenario VCM Bridge (USD)</h3>
          </div>
          
          {/* Dropdown Filters */}
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-1.5">
              <span className="text-[11px] uppercase tracking-wider text-muted-foreground">Material:</span>
              <MultiSelect
                label="Material"
                options={materials}
                selected={selectedMaterials}
                onChange={setSelectedMaterials}
              />
            </div>

            <div className="flex items-center gap-1.5">
              <span className="text-[11px] uppercase tracking-wider text-muted-foreground">Region:</span>
              <MultiSelect
                label="Region"
                options={regions.map(r => ({ id: r, name: r }))}
                selected={selectedRegions}
                onChange={setSelectedRegions}
              />
            </div>

            <button
              onClick={handleExportPPTX}
              disabled={exporting}
              className="h-8 px-3 rounded-md border border-primary/20 bg-primary/10 hover:bg-primary/20 text-primary text-[12px] font-semibold transition-all flex items-center gap-1.5 cursor-pointer disabled:opacity-50"
            >
              {exporting ? (
                <Loader2 className="size-3.5 animate-spin" />
              ) : (
                <Presentation className="size-3.5" />
              )}
              Export PPTX
            </button>
          </div>
        </div>

        {/* Custom SVG Waterfall Chart */}
        <div className="w-full overflow-x-auto select-none pt-2">
          <div className="min-w-[650px] relative">
            <svg viewBox={`0 0 700 ${chartHeight}`} className="w-full h-[280px]">
              {/* Draw horizontal reference lines */}
              <line x1="50" y1={getY(0)} x2="680" y2={getY(0)} stroke="var(--border)" strokeWidth="1.5" />

              {waterfallSteps.map((step, idx) => {
                const barWidth = 60;
                const barGap = 40;
                const startX = 60 + idx * (barWidth + barGap);
                
                const yStart = getY(step.start);
                const yEnd = getY(step.end);
                
                const top = Math.min(yStart, yEnd);
                const height = Math.abs(yStart - yEnd) || 2; // min 2px height
                const barColor = getBarColor(step);

                const isPositive = step.change > 0;
                const isNegative = step.change < 0;

                // Connection line to next bar
                const nextStep = waterfallSteps[idx + 1];
                let connectionLine = null;
                if (nextStep) {
                  const nextX = startX + barWidth;
                  const lineY = getY(step.end);
                  connectionLine = (
                    <line
                      x1={nextX}
                      y1={lineY}
                      x2={nextX + barGap}
                      y2={lineY}
                      stroke="var(--border)"
                      strokeWidth="1.2"
                      strokeDasharray="3 3"
                    />
                  );
                }

                return (
                  <g key={idx} className="group cursor-pointer">
                    {/* Connection Line */}
                    {connectionLine}

                    {/* Bar */}
                    <rect
                      x={startX}
                      y={top}
                      width={barWidth}
                      height={height}
                      fill={barColor}
                      rx="4"
                      className="transition-all duration-300 group-hover:opacity-90"
                    />

                    {/* Label above or below bar */}
                    <text
                      x={startX + barWidth / 2}
                      y={step.change >= 0 ? top - 8 : top + height + 16}
                      textAnchor="middle"
                      className="text-[10px] font-semibold font-mono"
                      fill={
                        step.type === "base" || step.type === "target"
                          ? "var(--foreground)"
                          : isPositive
                            ? "var(--positive)"
                            : isNegative
                              ? "var(--negative)"
                              : "var(--muted-foreground)"
                      }
                    >
                      {step.change > 0 && step.type === "var" ? "+" : ""}
                      {fmtCurrency(step.change, "USD")}
                    </text>

                    {/* Category Label at the bottom */}
                    <text
                      x={startX + barWidth / 2}
                      y={chartHeight - 12}
                      textAnchor="middle"
                      className="text-[10px] fill-muted-foreground font-semibold"
                    >
                      {step.label}
                    </text>
                  </g>
                );
              })}
            </svg>
          </div>
        </div>

        {/* Legend */}
        <div className="flex flex-wrap items-center gap-6 justify-center text-[12px] pt-2 border-t border-border/50">
          <div className="flex items-center gap-1.5">
            <div className="size-3.5 rounded bg-primary" style={{ backgroundColor: "var(--primary)" }} />
            <span className="text-muted-foreground font-medium">Scenario Totals</span>
          </div>
          <div className="flex items-center gap-1.5">
            <div className="size-3.5 rounded" style={{ backgroundColor: "var(--positive)" }} />
            <span className="text-muted-foreground font-medium">Positive Impact (+)</span>
          </div>
          <div className="flex items-center gap-1.5">
            <div className="size-3.5 rounded" style={{ backgroundColor: "var(--negative)" }} />
            <span className="text-muted-foreground font-medium">Negative Impact (-)</span>
          </div>
        </div>
      </div>

      {/* Detailed Breakdown Tables */}
      <div className="rounded-2xl border border-border bg-card shadow-elevated overflow-hidden">
        <div className="flex items-center justify-between px-4 py-3 border-b border-border">
          <div className="flex items-center gap-1 p-0.5 rounded-md bg-secondary">
            <button
              onClick={() => setActiveTab("material")}
              className={
                "h-8 px-3 text-[12px] font-medium rounded transition-colors cursor-pointer " +
                (activeTab === "material"
                  ? "bg-card text-foreground shadow-sm"
                  : "text-muted-foreground hover:text-foreground")
              }
            >
              Breakdown by Material
            </button>
            <button
              onClick={() => setActiveTab("month")}
              className={
                "h-8 px-3 text-[12px] font-medium rounded transition-colors cursor-pointer " +
                (activeTab === "month"
                  ? "bg-card text-foreground shadow-sm"
                  : "text-muted-foreground hover:text-foreground")
              }
            >
              Breakdown by Month
            </button>
          </div>
          <div className="text-[11px] uppercase tracking-[0.14em] text-muted-foreground">
            {activeTab === "material" ? by_material.length : by_month.length} entries
          </div>
        </div>

        <div className="max-h-[460px] overflow-auto">
          <table className="w-full text-[12px]">
            <thead className="sticky top-0 bg-card border-b border-border z-[1]">
              <tr>
                <th className="px-3 py-2 text-left uppercase tracking-[0.1em] text-muted-foreground font-medium">
                  {activeTab === "material" ? "Material" : "Period"}
                </th>
                <th className="px-3 py-2 text-right uppercase tracking-[0.1em] text-muted-foreground font-medium">Volume A</th>
                <th className="px-3 py-2 text-right uppercase tracking-[0.1em] text-muted-foreground font-medium">Volume B</th>
                <th className="px-3 py-2 text-right uppercase tracking-[0.1em] text-muted-foreground font-medium">VCM A (USD)</th>
                <th className="px-3 py-2 text-right uppercase tracking-[0.1em] text-muted-foreground font-medium">Volume Effect</th>
                <th className="px-3 py-2 text-right uppercase tracking-[0.1em] text-muted-foreground font-medium">Price Effect</th>
                <th className="px-3 py-2 text-right uppercase tracking-[0.1em] text-muted-foreground font-medium">Cost Effect</th>
                <th className="px-3 py-2 text-right uppercase tracking-[0.1em] text-muted-foreground font-medium">FX Effect</th>
                <th className="px-3 py-2 text-right uppercase tracking-[0.1em] text-muted-foreground font-medium">VCM B (USD)</th>
              </tr>
            </thead>
            <tbody>
              {activeTab === "material" ? (
                by_material.length === 0 ? (
                  <tr>
                    <td colSpan={9} className="text-center py-8 text-muted-foreground text-sm">
                      No material data matches the active filters.
                    </td>
                  </tr>
                ) : (
                  by_material.map((row, idx) => (
                    <tr key={idx} className="border-b border-border/60 hover:bg-secondary/40">
                      <td className="px-3 py-2 text-left">
                        <div className="font-medium text-foreground">{row.Material}</div>
                        <div className="text-[10px] text-muted-foreground font-mono">{row["Material ID"]}</div>
                      </td>
                      <td className="px-3 py-2 text-right tabular font-mono">{fmtVolume(row.Vol_A)}</td>
                      <td className="px-3 py-2 text-right tabular font-mono">{fmtVolume(row.Vol_B)}</td>
                      <td className="px-3 py-2 text-right tabular font-mono">{fmtCurrency(row.VCM_USD_A)}</td>
                      <td className="px-3 py-2 text-right"><DeltaSpan value={row.Volume_Effect} /></td>
                      <td className="px-3 py-2 text-right"><DeltaSpan value={row.Price_Effect} /></td>
                      <td className="px-3 py-2 text-right"><DeltaSpan value={row.Cost_Effect} /></td>
                      <td className="px-3 py-2 text-right"><DeltaSpan value={row.FX_Effect} /></td>
                      <td className="px-3 py-2 text-right tabular font-mono font-medium">{fmtCurrency(row.VCM_USD_B)}</td>
                    </tr>
                  ))
                )
              ) : (
                by_month.length === 0 ? (
                  <tr>
                    <td colSpan={9} className="text-center py-8 text-muted-foreground text-sm">
                      No monthly data matches the active filters.
                    </td>
                  </tr>
                ) : (
                  by_month.map((row, idx) => (
                    <tr key={idx} className="border-b border-border/60 hover:bg-secondary/40">
                      <td className="px-3 py-2 text-left font-semibold text-foreground font-mono">{row.Date}</td>
                      <td className="px-3 py-2 text-right tabular font-mono">{fmtVolume(row.Vol_A)}</td>
                      <td className="px-3 py-2 text-right tabular font-mono">{fmtVolume(row.Vol_B)}</td>
                      <td className="px-3 py-2 text-right tabular font-mono">{fmtCurrency(row.VCM_USD_A)}</td>
                      <td className="px-3 py-2 text-right"><DeltaSpan value={row.Volume_Effect} /></td>
                      <td className="px-3 py-2 text-right"><DeltaSpan value={row.Price_Effect} /></td>
                      <td className="px-3 py-2 text-right"><DeltaSpan value={row.Cost_Effect} /></td>
                      <td className="px-3 py-2 text-right"><DeltaSpan value={row.FX_Effect} /></td>
                      <td className="px-3 py-2 text-right tabular font-mono font-medium">{fmtCurrency(row.VCM_USD_B)}</td>
                    </tr>
                  ))
                )
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

function DeltaSpan({ value }: { value: number }) {
  if (value === 0) return <span className="tabular font-mono text-muted-foreground">$ 0</span>;
  const positive = value > 0;
  const Arrow = positive ? ArrowUpRight : ArrowDownRight;
  const colorClass = positive ? "text-positive" : "text-negative";

  return (
    <span className={`inline-flex items-center gap-0.5 tabular font-mono ${colorClass}`}>
      <Arrow className="size-3 shrink-0" />
      {fmtCurrency(value, "USD")}
    </span>
  );
}
