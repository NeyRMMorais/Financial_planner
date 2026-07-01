import { create } from "zustand";

export interface User {
  email: string;
  name: string;
  provider: 'google' | 'microsoft' | 'other';
}

export interface Scenario {
  name: string;
  created_at: string;
  base_scenario: string | null;
  description: string;
  change_log: string[];
  files_status?: Record<string, boolean>;
}

export interface Override {
  "Material ID": string;
  "Sold to ID": string;
  "Ship to ID": string;
  Date: string;
  Price: number;
}

export interface SummaryMetrics {
  total_volume: number;
  total_revenue_usd: number;
  total_revenue_lc: number;
  total_rm_cost_usd: number;
  total_rm_cost_lc: number;
  total_var_cost_usd: number;
  total_var_cost_lc: number;
  total_dist_cost_usd: number;
  total_dist_cost_lc: number;
  total_vcm_usd: number;
  total_vcm_lc: number;
  weighted_avg_price_usd: number;
  weighted_avg_price_lc: number;
  weighted_avg_vcm_usd: number;
  weighted_avg_vcm_lc: number;
}

export interface CompareMetrics {
  total_volume: number;
  total_revenue_usd: number;
  total_rm_cost_usd: number;
  total_var_cost_usd: number;
  total_dist_cost_usd: number;
  total_vcm_usd: number;
  weighted_avg_price_usd: number;
  weighted_avg_vcm_usd: number;
}

export interface PlantVariance {
  Plant: string;
  Volume_A: number;
  Volume_B: number;
  "Volume Delta": number;
  VCM_USD_A: number;
  VCM_USD_B: number;
  "VCM Delta": number;
}

export interface MaterialVariance {
  Material: string;
  "Material ID": string;
  Volume_A: number;
  Volume_B: number;
  "Volume Delta": number;
  VCM_USD_A: number;
  VCM_USD_B: number;
  "VCM Delta": number;
}

export interface CompareResult {
  absolute_diff: CompareMetrics;
  percentage_diff: Record<string, string>;
  change_log: string[];
  vcm_variance_by_plant: PlantVariance[];
  vcm_variance_by_material: MaterialVariance[];
}

export interface BridgeSummary {
  vcm_usd_a: number;
  volume_effect: number;
  price_effect: number;
  cost_effect: number;
  fx_effect: number;
  vcm_usd_b: number;
}

export interface BridgeResult {
  summary: BridgeSummary;
  by_material: any[];
  by_month: any[];
  raw_preview: any[];
}

export type FileType =
  | "volume_data"
  | "base_prices"
  | "base_costs"
  | "base_var_costs"
  | "base_dist_costs"
  | "fx_rates"
  | "plant_currency";

export const FILE_DEFS: { key: FileType; label: string; description: string }[] = [
  { key: "volume_data", label: "Volume Data", description: "Monthly planning volumes (MT)" },
  { key: "base_prices", label: "Base Prices", description: "Customer × Material pricing" },
  { key: "base_costs", label: "Raw Material Costs", description: "Monthly plant-specific RM costs" },
  { key: "base_var_costs", label: "Variable Costs", description: "Annual variable cost per material" },
  { key: "base_dist_costs", label: "Distribution Costs", description: "Annual distribution cost per ship-to" },
  { key: "fx_rates", label: "FX Rates", description: "Monthly USD exchange rates" },
  { key: "plant_currency", label: "Plant Currency", description: "Plant → Currency mapping" },
];

interface AppState {
  scenarios: Scenario[];
  selectedScenario: string | null;
  selectedScenarioMeta: Scenario | null;

  activePreviewTab: string;
  activeResultsTab: "revenue" | "rm_costs" | "var_costs" | "dist_costs" | "vcm";
  previewData: Record<string, any[]>;
  overrides: Override[];

  calculatedMetrics: SummaryMetrics | null;
  calculatedPreview: any[];
  currencyMode: "USD" | "LC";
  calculationError: string | null;

  loadingScenarios: boolean;
  loadingData: boolean;
  loadingCalculation: boolean;

  user: User | null;

  compareScenarioA: string;
  compareScenarioB: string;
  activeCompareScenarioA: string | null;
  activeCompareScenarioB: string | null;
  compareResult: CompareResult | null;
  bridgeResult: BridgeResult | null;
  loadingCompare: boolean;
  compareError: string | null;

  fetchScenarios: () => Promise<void>;
  selectScenario: (name: string) => Promise<void>;
  createScenario: (name: string, baseScenario: string | null, description: string) => Promise<void>;
  fetchScenarioData: (name: string, fileType: string) => Promise<void>;
  uploadScenarioFile: (fileType: string, file: File) => Promise<void>;
  addOverride: (override: Override) => Promise<void>;
  removeOverride: (index: number) => Promise<void>;
  calculateScenario: () => Promise<void>;
  runComparison: () => Promise<void>;
  setCurrencyMode: (mode: "USD" | "LC") => void;
  setActivePreviewTab: (tab: string) => void;
  setActiveResultsTab: (tab: AppState["activeResultsTab"]) => void;
  setCompareScenarioA: (name: string) => void;
  setCompareScenarioB: (name: string) => void;
  loginUser: (email: string, name: string, provider: 'google' | 'microsoft' | 'other') => Promise<void>;
  logoutUser: () => void;
  fetchLoginLogs: (email: string) => Promise<any[]>;
  exportBridgePPTX: (payload: {
    scenario_a: string;
    scenario_b: string;
    vcm_usd_a: number;
    volume_effect: number;
    price_effect: number;
    cost_effect: number;
    fx_effect: number;
    vcm_usd_b: number;
    material_filter: string;
    region_filter: string;
  }) => Promise<void>;
  validateAndDiffScenarioFile: (fileType: string, file: File) => Promise<{
    status: string;
    is_new: boolean;
    diff: string[];
    volume_delta_by_material?: any[];
    price_delta_by_material?: any[];
    var_cost_delta_by_material?: any[];
    fx_delta_by_currency?: any[];
  }>;
}

export const useAppStore = create<AppState>((set, get) => ({
  scenarios: [],
  selectedScenario: null,
  selectedScenarioMeta: null,

  activePreviewTab: "volume_data",
  activeResultsTab: "revenue",
  previewData: {},
  overrides: [],

  calculatedMetrics: null,
  calculatedPreview: [],
  currencyMode: "USD",
  calculationError: null,

  loadingScenarios: false,
  loadingData: false,
  loadingCalculation: false,

  user: (() => {
    try {
      const stored = localStorage.getItem("planner_user");
      return stored ? JSON.parse(stored) : null;
    } catch {
      return null;
    }
  })(),

  compareScenarioA: "",
  compareScenarioB: "",
  activeCompareScenarioA: null,
  activeCompareScenarioB: null,
  compareResult: null,
  bridgeResult: null,
  loadingCompare: false,
  compareError: null,

  loginUser: async (email, name, provider) => {
    const userObj = { email, name, provider };
    try {
      // POST the login-log to backend
      const res = await fetch("/api/login-log", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(userObj),
      });
      if (res.ok) {
        localStorage.setItem("planner_user", JSON.stringify(userObj));
        set({ user: userObj });
      } else {
        throw new Error("Failed to register access in backend audit logs");
      }
    } catch (err) {
      console.error("Login logging failed:", err);
      // Still set the user state locally for development / fallback flow
      localStorage.setItem("planner_user", JSON.stringify(userObj));
      set({ user: userObj });
    }
  },

  logoutUser: () => {
    localStorage.removeItem("planner_user");
    set({ user: null });
  },

  fetchLoginLogs: async (email) => {
    const res = await fetch(`/api/admin/login-logs?email=${encodeURIComponent(email)}`);
    if (!res.ok) {
      if (res.status === 403) throw new Error("Forbidden: Admin access only");
      throw new Error("Failed to load audit logs");
    }
    return res.json();
  },

  exportBridgePPTX: async (payload) => {
    const res = await fetch("/api/export/bridge-pptx", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!res.ok) throw new Error("Failed to export PPTX");
    
    const blob = await res.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `vcm_waterfall_bridge_${payload.scenario_a}_vs_${payload.scenario_b}.pptx`;
    document.body.appendChild(a);
    a.click();
    a.remove();
    window.URL.revokeObjectURL(url);
  },

  fetchScenarios: async () => {
    set({ loadingScenarios: true });
    try {
      const res = await fetch("/api/scenarios");
      if (!res.ok) throw new Error("Failed to load scenarios");
      const data = await res.json();
      set({ scenarios: data });
      if (data.length > 0 && !get().selectedScenario) {
        const baseline = data.find((s: Scenario) => s.name === "Baseline") || data[0];
        get().selectScenario(baseline.name);
      }
    } catch (err) {
      console.error(err);
    } finally {
      set({ loadingScenarios: false });
    }
  },

  selectScenario: async (name: string) => {
    set({ selectedScenario: name, loadingData: true, calculationError: null });
    try {
      const metaRes = await fetch(`/api/scenarios/${name}/metadata`);
      if (!metaRes.ok) throw new Error("Failed to fetch metadata");
      const meta = await metaRes.json();
      set({ selectedScenarioMeta: meta });

      const activeTab = get().activePreviewTab;
      await Promise.all([
        get().fetchScenarioData(name, activeTab),
        get().fetchScenarioData(name, "price_overrides"),
      ]);
      await get().calculateScenario();
    } catch (err: any) {
      set({ calculationError: err.message });
    } finally {
      set({ loadingData: false });
    }
  },

  createScenario: async (name, baseScenario, description) => {
    const res = await fetch("/api/scenarios", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, base_scenario: baseScenario, description }),
    });
    if (!res.ok) {
      const errorDetail = await res.json().catch(() => ({}));
      throw new Error(errorDetail.detail || "Failed to create scenario");
    }
    await get().fetchScenarios();
    await get().selectScenario(name);
  },

  fetchScenarioData: async (name, fileType) => {
    try {
      const res = await fetch(`/api/scenarios/${name}/data/${fileType}`);
      if (!res.ok) throw new Error(`Failed to load ${fileType}`);
      const fileData = await res.json();
      if (fileType === "price_overrides") {
        set({ overrides: fileData });
      } else {
        set((state) => ({ previewData: { ...state.previewData, [fileType]: fileData } }));
      }
    } catch (err) {
      console.error(err);
    }
  },

  uploadScenarioFile: async (fileType, file) => {
    const name = get().selectedScenario;
    if (!name) return;
    set({ loadingData: true, calculationError: null });
    const formData = new FormData();
    formData.append("file", file);
    try {
      const res = await fetch(`/api/scenarios/${name}/upload/${fileType}`, {
        method: "POST",
        body: formData,
      });
      if (!res.ok) {
        const errorDetail = await res.json().catch(() => ({}));
        throw new Error(errorDetail.detail || "Upload failed");
      }
      await get().fetchScenarioData(name, fileType);
      await get().calculateScenario();
      const metaRes = await fetch(`/api/scenarios/${name}/metadata`);
      const meta = await metaRes.json();
      set({ selectedScenarioMeta: meta });
    } catch (err: any) {
      set({ calculationError: err.message });
      throw err;
    } finally {
      set({ loadingData: false });
    }
  },

  validateAndDiffScenarioFile: async (fileType, file) => {
    const name = get().selectedScenario;
    if (!name) throw new Error("No scenario selected");
    const formData = new FormData();
    formData.append("file", file);
    const res = await fetch(`/api/scenarios/${name}/diff-file/${fileType}`, {
      method: "POST",
      body: formData,
    });
    if (!res.ok) {
      const errorDetail = await res.json().catch(() => ({}));
      throw new Error(errorDetail.detail || "Validation failed");
    }
    return await res.json();
  },

  addOverride: async (override) => {
    const name = get().selectedScenario;
    if (!name) return;
    const existingIdx = get().overrides.findIndex(
      (o) =>
        o["Material ID"] === override["Material ID"] &&
        o["Sold to ID"] === override["Sold to ID"] &&
        o["Ship to ID"] === override["Ship to ID"] &&
        o.Date === override.Date,
    );
    const updated = [...get().overrides];
    if (existingIdx >= 0) updated[existingIdx] = override;
    else updated.push(override);
    set({ overrides: updated, loadingCalculation: true });
    try {
      const res = await fetch(`/api/scenarios/${name}/overrides`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(updated),
      });
      if (!res.ok) throw new Error("Failed to update overrides");
      await get().calculateScenario();
    } catch (err: any) {
      set({ calculationError: err.message });
    } finally {
      set({ loadingCalculation: false });
    }
  },

  removeOverride: async (index) => {
    const name = get().selectedScenario;
    if (!name) return;
    const updated = get().overrides.filter((_, i) => i !== index);
    set({ overrides: updated, loadingCalculation: true });
    try {
      const res = await fetch(`/api/scenarios/${name}/overrides`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(updated),
      });
      if (!res.ok) throw new Error("Failed to remove override");
      await get().calculateScenario();
    } catch (err: any) {
      set({ calculationError: err.message });
    } finally {
      set({ loadingCalculation: false });
    }
  },

  calculateScenario: async () => {
    const name = get().selectedScenario;
    if (!name) return;
    set({ loadingCalculation: true, calculationError: null });
    try {
      const res = await fetch(`/api/scenarios/${name}/calculate`, { method: "POST" });
      if (!res.ok) {
        const errorDetail = await res.json().catch(() => ({}));
        throw new Error(errorDetail.detail || "Calculation pipeline failed");
      }
      const calcResult = await res.json();
      set({ calculatedMetrics: calcResult.metrics, calculatedPreview: calcResult.preview });
    } catch (err: any) {
      set({ calculationError: err.message, calculatedMetrics: null, calculatedPreview: [] });
    } finally {
      set({ loadingCalculation: false });
    }
  },

  runComparison: async () => {
    const { compareScenarioA, compareScenarioB } = get();
    if (!compareScenarioA || !compareScenarioB) return;
    if (compareScenarioA === compareScenarioB) {
      set({ compareError: "Please select two different scenarios.", compareResult: null, bridgeResult: null });
      return;
    }
    set({ loadingCompare: true, compareError: null, compareResult: null, bridgeResult: null });
    try {
      const [resCompare, resBridge] = await Promise.all([
        fetch("/api/compare", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ scenario_a: compareScenarioA, scenario_b: compareScenarioB }),
        }),
        fetch("/api/compare/bridge", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ scenario_a: compareScenarioA, scenario_b: compareScenarioB }),
        })
      ]);

      if (!resCompare.ok) {
        const errorDetail = await resCompare.json().catch(() => ({}));
        throw new Error(errorDetail.detail || "Comparison pipeline failed");
      }
      if (!resBridge.ok) {
        const errorDetail = await resBridge.json().catch(() => ({}));
        throw new Error(errorDetail.detail || "Bridge calculation failed");
      }

      const compareData = await resCompare.json();
      const bridgeData = await resBridge.json();
      set({
        compareResult: compareData,
        bridgeResult: bridgeData,
        activeCompareScenarioA: compareScenarioA,
        activeCompareScenarioB: compareScenarioB,
      });
    } catch (err: any) {
      set({ compareError: err.message });
    } finally {
      set({ loadingCompare: false });
    }
  },

  setCurrencyMode: (mode) => set({ currencyMode: mode }),
  setActivePreviewTab: (tab) => {
    set({ activePreviewTab: tab });
    const name = get().selectedScenario;
    if (name) get().fetchScenarioData(name, tab);
  },
  setActiveResultsTab: (tab) => set({ activeResultsTab: tab }),
  setCompareScenarioA: (name) => set({ compareScenarioA: name }),
  setCompareScenarioB: (name) => set({ compareScenarioB: name }),
}));
