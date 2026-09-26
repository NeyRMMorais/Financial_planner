import { useMemo, useState, useEffect, useRef } from "react";
import { useAppStore, BridgeResult } from "@/store/useAppStore";
import { fmtCurrency, fmtVolume } from "@/lib/format";
import { ArrowUpRight, ArrowDownRight, ChevronDown, Search, Presentation, Loader2, Layers, Sparkles } from "lucide-react";

interface BridgeWaterfallProps {
  data: BridgeResult;
}

// Map material to chemical product line
export function getProductLine(materialId: string, materialName: string = ""): string {
  const mId = (materialId || "").toUpperCase().trim();
  const mName = (materialName || "").toUpperCase().trim();
  if (mId.includes("MAT-1001") || mId.includes("MAT-3098") || mName.includes("RESIN") || mName.includes("SPECIALTY")) {
    return "Line 1 - Performance Specialties";
  } else if (mId.includes("MAT-2004") || mId.includes("MAT-4120") || mName.includes("ADDITIVE") || mName.includes("FILM")) {
    return "Line 2 - Functional Formulations";
  } else if (mId.includes("MAT-5185") || mName.includes("POLYMER") || mName.includes("BASE") || mName.includes("INTERMEDIATE")) {
    return "Line 3 - Base Intermediates";
  } else {
    if (mId.includes("1") || mId.includes("3")) return "Line 1 - Performance Specialties";
    if (mId.includes("2") || mId.includes("4")) return "Line 2 - Functional Formulations";
    return "Line 3 - Base Intermediates";
  }
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
                  className="rounded border-border text-primary focus:ring-primary size-3.5"
                />
                <span className="font-semibold text-foreground">Select All</span>
              </label>
            </div>

            {/* Individual items */}
            <div className="py-1 space-y-0.5">
              {filteredOptions.length === 0 ? (
                <div className="px-2 py-2 text-[11px] text-muted-foreground text-center">
                  No {label.toLowerCase()}s match search
                </div>
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
                        className="rounded border-border text-primary focus:ring-primary size-3.5"
                      />
                      <span className="truncate text-foreground" title={opt.name}>
                        {opt.name}
                      </span>
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
  const [activeTab, setActiveTab] = useState<"product_line" | "material" | "month">("product_line");
  const [selectedMaterials, setSelectedMaterials] = useState<string[]>([]);
  const [selectedRegions, setSelectedRegions] = useState<string[]>([]);
  const [exporting, setExporting] = useState(false);
  const tableRef = useRef<HTMLDivElement>(null);

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

  // Extract unique regions
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

  // Re-calculate 6-pillar summary metrics dynamically across filtered records
  const summary = useMemo(() => {
    let vcm_usd_a = 0;
    let total_vol_a = 0;
    let total_vol_b = 0;
    let volume_effect = 0;
    let price_effect = 0;
    let cost_effect = 0;
    let fx_effect = 0;
    let vcm_usd_b = 0;

    filteredRows.forEach((row) => {
      vcm_usd_a += Number(row.VCM_USD_A) || 0;
      total_vol_a += Number(row.Vol_A) || 0;
      total_vol_b += Number(row.Vol_B) || 0;
      volume_effect += Number(row.Volume_Effect) || 0;
      price_effect += Number(row.Price_Effect) || 0;
      cost_effect += Number(row.Cost_Effect) || 0;
      fx_effect += Number(row.FX_Effect) || 0;
      vcm_usd_b += Number(row.VCM_USD_B) || 0;
    });

    // Baseline portfolio gross unit margin in USD
    const base_unit_margin = total_vol_a > 0 ? vcm_usd_a / total_vol_a : 0;
    // Pure Volume Effect = (Total_Vol_B - Total_Vol_A) * Baseline Portfolio Unit Margin
    const pure_volume_effect = (total_vol_b - total_vol_a) * base_unit_margin;
    // Mix Effect = Total Volume Variance - Pure Volume Effect
    const mix_effect = volume_effect - pure_volume_effect;

    return {
      vcm_usd_a,
      total_vol_a,
      total_vol_b,
      base_unit_margin,
      pure_volume_effect,
      mix_effect,
      volume_effect,
      price_effect,
      cost_effect,
      fx_effect,
      vcm_usd_b,
    };
  }, [filteredRows]);

  // Re-group by Product Line (Chemical Portfolio Hierarchy)
  const by_product_line = useMemo(() => {
    const groups: Record<string, any> = {};
    const baseUnitMargin = summary.base_unit_margin;

    filteredRows.forEach((row) => {
      const line = getProductLine(row["Material ID"], row["Material"]);
      if (!groups[line]) {
        groups[line] = {
          product_line: line,
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
      groups[line].Vol_A += Number(row.Vol_A) || 0;
      groups[line].Vol_B += Number(row.Vol_B) || 0;
      groups[line].VCM_USD_A += Number(row.VCM_USD_A) || 0;
      groups[line].VCM_USD_B += Number(row.VCM_USD_B) || 0;
      groups[line].Volume_Effect += Number(row.Volume_Effect) || 0;
      groups[line].Price_Effect += Number(row.Price_Effect) || 0;
      groups[line].Cost_Effect += Number(row.Cost_Effect) || 0;
      groups[line].FX_Effect += Number(row.FX_Effect) || 0;
    });

    return Object.values(groups).map((g: any) => {
      const volDelta = g.Vol_B - g.Vol_A;
      const vcmDelta = g.VCM_USD_B - g.VCM_USD_A;
      const pureVol = volDelta * baseUnitMargin;
      const mixEff = g.Volume_Effect - pureVol;
      const volGrowthPct = g.Vol_A > 0 ? (volDelta / g.Vol_A) * 100 : 0;
      const unitVcmA = g.Vol_A > 0 ? g.VCM_USD_A / g.Vol_A : 0;
      const unitVcmB = g.Vol_B > 0 ? g.VCM_USD_B / g.Vol_B : 0;

      return {
        ...g,
        vol_delta: volDelta,
        vcm_delta: vcmDelta,
        pure_volume_effect: pureVol,
        mix_effect: mixEff,
        volume_growth_pct: volGrowthPct,
        unit_vcm_usd_a: unitVcmA,
        unit_vcm_usd_b: unitVcmB,
      };
    }).sort((a, b) => a.product_line.localeCompare(b.product_line));
  }, [filteredRows, summary.base_unit_margin]);

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
          Product_Line: getProductLine(id, name),
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

  // Prepare steps for 6-pillar waterfall chart (Base -> Pure Vol -> Mix -> Price -> Cost -> FX -> Target)
  const waterfallSteps = useMemo(() => {
    const s = summary;
    const base = Number(s.vcm_usd_a);
    const pureVol = Number(s.pure_volume_effect);
    const mix = Number(s.mix_effect);
    const price = Number(s.price_effect);
    const cost = Number(s.cost_effect);
    const fx = Number(s.fx_effect);
    const target = Number(s.vcm_usd_b);

    const step1 = base;
    const step2 = step1 + pureVol;
    const step3 = step2 + mix;
    const step4 = step3 + price;
    const step5 = step4 + cost;
    const step6 = step5 + fx;

    return [
      { label: activeCompareScenarioA || "Base VCM", start: 0, end: base, change: base, type: "base" as const, isInteractive: false },
      { label: "Pure Volume", start: step1, end: step2, change: pureVol, type: "var" as const, isInteractive: false },
      { label: "Mix Effect", start: step2, end: step3, change: mix, type: "var" as const, isInteractive: true },
      { label: "Price Effect", start: step3, end: step4, change: price, type: "var" as const, isInteractive: false },
      { label: "Cost Effect", start: step4, end: step5, change: cost, type: "var" as const, isInteractive: false },
      { label: "FX Effect", start: step5, end: step6, change: fx, type: "var" as const, isInteractive: false },
      { label: activeCompareScenarioB || "Target VCM", start: 0, end: target, change: target, type: "target" as const, isInteractive: false },
    ];
  }, [summary, activeCompareScenarioA, activeCompareScenarioB]);

  // Find min/max values for scaling the SVG chart
  const scale = useMemo(() => {
    const base = Number(summary.vcm_usd_a);
    const pureVol = Number(summary.pure_volume_effect);
    const mix = Number(summary.mix_effect);
    const price = Number(summary.price_effect);
    const cost = Number(summary.cost_effect);
    const target = Number(summary.vcm_usd_b);

    const runningValues = [
      0,
      base,
      base + pureVol,
      base + pureVol + mix,
      base + pureVol + mix + price,
      base + pureVol + mix + price + cost,
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

  const handleMixClick = () => {
    setActiveTab("product_line");
    tableRef.current?.scrollIntoView({ behavior: "smooth" });
  };

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

      const isDark = document.documentElement.classList.contains("dark");

      await exportBridgePPTX({
        scenario_a: activeCompareScenarioA || "Base VCM",
        scenario_b: activeCompareScenarioB || "Target VCM",
        vcm_usd_a: Number(summary.vcm_usd_a),
        pure_volume_effect: Number(summary.pure_volume_effect),
        mix_effect: Number(summary.mix_effect),
        volume_effect: Number(summary.volume_effect),
        price_effect: Number(summary.price_effect),
        cost_effect: Number(summary.cost_effect),
        fx_effect: Number(summary.fx_effect),
        vcm_usd_b: Number(summary.vcm_usd_b),
        material_filter: matFilterText,
        region_filter: regFilterText,
        theme: isDark ? "dark" : "light",
        commentary: data.commentary
      });
    } catch (err) {
      console.error(err);
      alert("Failed to export PowerPoint slide");
    } finally {
      setExporting(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Waterfall Visualizer */}
      <div className="rounded-2xl border border-border bg-card p-6 shadow-elevated space-y-4">
        {/* Header containing Title and Filters */}
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2">
              <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-primary/10 text-primary uppercase tracking-wider">
                Phase 1 Executive Standard
              </span>
              <span className="text-[11px] uppercase tracking-[0.14em] text-muted-foreground">6-Pillar PVM + FX Bridge</span>
            </div>
            <h3 className="text-lg font-semibold mt-1">Scenario Gross Margin Bridge (USD)</h3>
          </div>
          
          {/* Dropdown Filters & Actions */}
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

        {/* 6-Pillar SVG Waterfall Chart */}
        <div className="w-full overflow-x-auto select-none pt-2">
          <div className="min-w-[720px] relative">
            <svg viewBox={`0 0 760 ${chartHeight}`} className="w-full h-[280px]">
              {/* Draw horizontal reference line at 0 */}
              <line x1="30" y1={getY(0)} x2="740" y2={getY(0)} stroke="var(--border)" strokeWidth="1.5" />

              {waterfallSteps.map((step, idx) => {
                const barWidth = 54;
                const barGap = 34;
                const startX = 40 + idx * (barWidth + barGap);
                
                const yStart = getY(step.start);
                const yEnd = getY(step.end);
                
                const top = Math.min(yStart, yEnd);
                const height = Math.abs(yStart - yEnd) || 2;
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
                  <g
                    key={idx}
                    className={`group ${step.isInteractive ? 'cursor-pointer' : ''}`}
                    onClick={step.isInteractive ? handleMixClick : undefined}
                  >
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
                      className={`transition-all duration-300 group-hover:opacity-90 ${
                        step.isInteractive ? 'ring-2 ring-primary/40 stroke-primary/30 stroke-1' : ''
                      }`}
                    />

                    {/* Value label above or below bar */}
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

                    {/* Category Label at bottom */}
                    <text
                      x={startX + barWidth / 2}
                      y={chartHeight - 14}
                      textAnchor="middle"
                      className={`text-[10px] font-semibold ${
                        step.isInteractive ? 'fill-primary font-bold underline' : 'fill-muted-foreground'
                      }`}
                    >
                      {step.label}
                    </text>

                    {step.isInteractive && (
                      <text
                        x={startX + barWidth / 2}
                        y={chartHeight - 2}
                        textAnchor="middle"
                        className="text-[8px] fill-primary/80 font-medium"
                      >
                        (drilldown 🔍)
                      </text>
                    )}
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
          <div className="flex items-center gap-1.5">
            <span className="px-1.5 py-0.5 rounded text-[10px] bg-primary/10 text-primary font-semibold">Mix Effect</span>
            <span className="text-muted-foreground font-medium">Click bar to drill down</span>
          </div>
        </div>
      </div>

      {/* 3-Card Mix & Volume Executive Highlight Callouts */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Pure Volume Callout */}
        <div className="rounded-xl border border-border bg-card p-4 shadow-elevated">
          <div className="flex items-center justify-between">
            <span className="text-[11px] uppercase tracking-[0.14em] text-muted-foreground font-medium">Pure Volume Effect</span>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-secondary text-foreground">
              Baseline Unit: {fmtCurrency(summary.base_unit_margin, "USD")}/MT
            </span>
          </div>
          <div className="mt-2 text-xl font-bold font-mono">
            <DeltaSpan value={summary.pure_volume_effect} />
          </div>
          <div className="mt-1 text-[11px] text-muted-foreground">
            Volume shift: {fmtVolume(summary.total_vol_b - summary.total_vol_a)} MT from {fmtVolume(summary.total_vol_a)} MT baseline.
          </div>
        </div>

        {/* Portfolio Mix Callout */}
        <div
          onClick={handleMixClick}
          className="rounded-xl border border-primary/30 bg-card hover:bg-card/80 transition-all p-4 shadow-elevated cursor-pointer group"
        >
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-1.5">
              <span className="text-[11px] uppercase tracking-[0.14em] text-primary font-semibold">Portfolio Mix Shift</span>
              <Sparkles className="size-3 text-primary animate-pulse" />
            </div>
            <span className="text-[10px] text-primary underline group-hover:font-semibold">View Lines →</span>
          </div>
          <div className="mt-2 text-xl font-bold font-mono">
            <DeltaSpan value={summary.mix_effect} />
          </div>
          <div className="mt-1 text-[11px] text-muted-foreground">
            {summary.mix_effect >= 0
              ? "Favorable shift towards higher-margin product lines."
              : "Unfavorable drag from higher volume in lower-margin lines."}
          </div>
        </div>

        {/* Total Volume Variance Callout */}
        <div className="rounded-xl border border-border bg-card p-4 shadow-elevated">
          <div className="flex items-center justify-between">
            <span className="text-[11px] uppercase tracking-[0.14em] text-muted-foreground font-medium">Total Volume Variance</span>
            <span className="text-[10px] text-muted-foreground font-mono">Pure Vol + Mix</span>
          </div>
          <div className="mt-2 text-xl font-bold font-mono">
            <DeltaSpan value={summary.volume_effect} />
          </div>
          <div className="mt-1 text-[11px] text-muted-foreground">
            Reconciles exactly: {fmtCurrency(summary.pure_volume_effect, "USD")} + {fmtCurrency(summary.mix_effect, "USD")}.
          </div>
        </div>
      </div>

      {/* Commentary Card */}
      {data.commentary && data.commentary.length > 0 && (() => {
        const isAI = data.commentary[0] === "[AI-Generated Summary]";
        const bullets = data.commentary.slice(1);
        
        return (
          <div className="rounded-2xl border border-border bg-card p-6 shadow-elevated space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div className="p-1.5 rounded-lg bg-primary/10 text-primary">
                  <Presentation className="size-4" />
                </div>
                <h3 className="text-sm font-semibold text-foreground tracking-tight">Bridge Driver Insights</h3>
              </div>
              <span className={`px-2.5 py-0.5 rounded-full text-[10px] font-semibold ${isAI ? 'bg-gradient-brand text-white shadow-glow' : 'bg-secondary text-muted-foreground'}`}>
                {isAI ? 'AI-Synthesized' : 'Rule-Based Fallback'}
              </span>
            </div>
            
            <ul className="space-y-3 text-[13px] text-muted-foreground pl-1">
              {bullets.map((bullet, idx) => {
                const parts = bullet.split("**");
                const formattedText = parts.map((part, pIdx) => {
                  if (pIdx % 2 === 1) {
                    return <strong key={pIdx} className="font-semibold text-foreground">{part}</strong>;
                  }
                  return part;
                });
                
                return (
                  <li key={idx} className="flex items-start gap-2.5 leading-relaxed">
                    <span className="size-1.5 rounded-full bg-primary/60 shrink-0 mt-2" />
                    <span>{formattedText}</span>
                  </li>
                );
              })}
            </ul>
          </div>
        );
      })()}

      {/* Detailed Breakdown Tables */}
      <div ref={tableRef} className="rounded-2xl border border-border bg-card shadow-elevated overflow-hidden">
        <div className="flex items-center justify-between px-4 py-3 border-b border-border">
          <div className="flex items-center gap-1 p-0.5 rounded-md bg-secondary">
            <button
              onClick={() => setActiveTab("product_line")}
              className={
                "h-8 px-3 text-[12px] font-medium rounded transition-colors cursor-pointer flex items-center gap-1.5 " +
                (activeTab === "product_line"
                  ? "bg-card text-foreground shadow-sm font-semibold"
                  : "text-muted-foreground hover:text-foreground")
              }
            >
              <Layers className="size-3.5" />
              Breakdown by Product Line (Mix Drilldown)
            </button>
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
            {activeTab === "product_line"
              ? `${by_product_line.length} lines`
              : activeTab === "material"
                ? `${by_material.length} materials`
                : `${by_month.length} months`}
          </div>
        </div>

        <div className="max-h-[460px] overflow-auto">
          {activeTab === "product_line" ? (
            <table className="w-full text-[12px]">
              <thead className="sticky top-0 bg-card border-b border-border z-[1]">
                <tr>
                  <th className="px-3 py-2 text-left uppercase tracking-[0.1em] text-muted-foreground font-medium">Chemical Product Line</th>
                  <th className="px-3 py-2 text-right uppercase tracking-[0.1em] text-muted-foreground font-medium">Vol A (MT)</th>
                  <th className="px-3 py-2 text-right uppercase tracking-[0.1em] text-muted-foreground font-medium">Vol B (MT)</th>
                  <th className="px-3 py-2 text-right uppercase tracking-[0.1em] text-muted-foreground font-medium">Vol Growth</th>
                  <th className="px-3 py-2 text-right uppercase tracking-[0.1em] text-muted-foreground font-medium">VCM A (USD)</th>
                  <th className="px-3 py-2 text-right uppercase tracking-[0.1em] text-muted-foreground font-medium">Pure Vol Effect</th>
                  <th className="px-3 py-2 text-right uppercase tracking-[0.1em] text-primary font-bold">Mix Effect</th>
                  <th className="px-3 py-2 text-right uppercase tracking-[0.1em] text-muted-foreground font-medium">Price Effect</th>
                  <th className="px-3 py-2 text-right uppercase tracking-[0.1em] text-muted-foreground font-medium">Cost Effect</th>
                  <th className="px-3 py-2 text-right uppercase tracking-[0.1em] text-muted-foreground font-medium">FX Effect</th>
                  <th className="px-3 py-2 text-right uppercase tracking-[0.1em] text-muted-foreground font-medium">VCM B (USD)</th>
                </tr>
              </thead>
              <tbody>
                {by_product_line.length === 0 ? (
                  <tr>
                    <td colSpan={11} className="text-center py-8 text-muted-foreground text-sm">
                      No product line data matches the active filters.
                    </td>
                  </tr>
                ) : (
                  by_product_line.map((line, idx) => (
                    <tr key={idx} className="border-b border-border/60 hover:bg-secondary/40">
                      <td className="px-3 py-2 text-left">
                        <div className="font-semibold text-foreground">{line.product_line}</div>
                        <div className="text-[10px] text-muted-foreground">
                          Unit Margin: {fmtCurrency(line.unit_vcm_usd_a)}/MT → {fmtCurrency(line.unit_vcm_usd_b)}/MT
                        </div>
                      </td>
                      <td className="px-3 py-2 text-right tabular font-mono">{fmtVolume(line.Vol_A)}</td>
                      <td className="px-3 py-2 text-right tabular font-mono">{fmtVolume(line.Vol_B)}</td>
                      <td className="px-3 py-2 text-right tabular font-mono">
                        <span className={line.volume_growth_pct >= 0 ? "text-positive" : "text-negative"}>
                          {line.volume_growth_pct >= 0 ? "+" : ""}{line.volume_growth_pct.toFixed(1)}%
                        </span>
                      </td>
                      <td className="px-3 py-2 text-right tabular font-mono">{fmtCurrency(line.VCM_USD_A)}</td>
                      <td className="px-3 py-2 text-right"><DeltaSpan value={line.pure_volume_effect} /></td>
                      <td className="px-3 py-2 text-right bg-primary/5 font-semibold"><DeltaSpan value={line.mix_effect} /></td>
                      <td className="px-3 py-2 text-right"><DeltaSpan value={line.Price_Effect} /></td>
                      <td className="px-3 py-2 text-right"><DeltaSpan value={line.Cost_Effect} /></td>
                      <td className="px-3 py-2 text-right"><DeltaSpan value={line.FX_Effect} /></td>
                      <td className="px-3 py-2 text-right tabular font-mono font-semibold">{fmtCurrency(line.VCM_USD_B)}</td>
                    </tr>
                  ))
                )}
              </tbody>
              <tfoot className="border-t border-border font-bold bg-secondary/30">
                <tr>
                  <td className="px-3 py-2 text-left">Portfolio Total</td>
                  <td className="px-3 py-2 text-right tabular font-mono">{fmtVolume(summary.total_vol_a)}</td>
                  <td className="px-3 py-2 text-right tabular font-mono">{fmtVolume(summary.total_vol_b)}</td>
                  <td className="px-3 py-2 text-right tabular font-mono">
                    {summary.total_vol_a > 0
                      ? `${(((summary.total_vol_b - summary.total_vol_a) / summary.total_vol_a) * 100).toFixed(1)}%`
                      : "0.0%"}
                  </td>
                  <td className="px-3 py-2 text-right tabular font-mono">{fmtCurrency(summary.vcm_usd_a)}</td>
                  <td className="px-3 py-2 text-right"><DeltaSpan value={summary.pure_volume_effect} /></td>
                  <td className="px-3 py-2 text-right bg-primary/10 font-bold"><DeltaSpan value={summary.mix_effect} /></td>
                  <td className="px-3 py-2 text-right"><DeltaSpan value={summary.price_effect} /></td>
                  <td className="px-3 py-2 text-right"><DeltaSpan value={summary.cost_effect} /></td>
                  <td className="px-3 py-2 text-right"><DeltaSpan value={summary.fx_effect} /></td>
                  <td className="px-3 py-2 text-right tabular font-mono">{fmtCurrency(summary.vcm_usd_b)}</td>
                </tr>
              </tfoot>
            </table>
          ) : activeTab === "material" ? (
            <table className="w-full text-[12px]">
              <thead className="sticky top-0 bg-card border-b border-border z-[1]">
                <tr>
                  <th className="px-3 py-2 text-left uppercase tracking-[0.1em] text-muted-foreground font-medium">Material</th>
                  <th className="px-3 py-2 text-left uppercase tracking-[0.1em] text-muted-foreground font-medium">Product Line</th>
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
                {by_material.length === 0 ? (
                  <tr>
                    <td colSpan={10} className="text-center py-8 text-muted-foreground text-sm">
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
                      <td className="px-3 py-2 text-left text-[11px] text-muted-foreground">{row.Product_Line}</td>
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
                )}
              </tbody>
            </table>
          ) : (
            <table className="w-full text-[12px]">
              <thead className="sticky top-0 bg-card border-b border-border z-[1]">
                <tr>
                  <th className="px-3 py-2 text-left uppercase tracking-[0.1em] text-muted-foreground font-medium">Period</th>
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
                {by_month.length === 0 ? (
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
                )}
              </tbody>
            </table>
          )}
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
