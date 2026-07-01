import { useRef, useState } from "react";
import { FILE_DEFS, useAppStore, type Override } from "@/store/useAppStore";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import { Check, CircleAlert, Eye, Loader2, Trash2, Upload, Plus, Download } from "lucide-react";
import { fmtNumber } from "@/lib/format";



function FileCard({ fileKey, label, description }: { fileKey: string; label: string; description: string }) {
  const {
    selectedScenarioMeta,
    uploadScenarioFile,
    validateAndDiffScenarioFile,
    fetchScenarioData,
    previewData,
    selectedScenario,
    loadingData,
  } = useAppStore();

  const inputRef = useRef<HTMLInputElement>(null);
  const [openPreview, setOpenPreview] = useState(false);
  const [openConfirm, setOpenConfirm] = useState(false);
  const [validating, setValidating] = useState(false);
  const [validationError, setValidationError] = useState<string | null>(null);
  const [diffResult, setDiffResult] = useState<any | null>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  const present = !!selectedScenarioMeta?.files_status?.[fileKey];
  const data = previewData[fileKey] || [];

  const onChoose = () => {
    if (inputRef.current) {
      inputRef.current.value = "";
    }
    inputRef.current?.click();
  };

  const handleFileChange = async (f: File | null) => {
    if (!f) return;
    setSelectedFile(f);
    setValidating(true);
    setValidationError(null);
    setDiffResult(null);
    try {
      const result = await validateAndDiffScenarioFile(fileKey, f);
      setDiffResult(result);
      setOpenConfirm(true);
    } catch (err: any) {
      setValidationError(err.message || "An unexpected error occurred during validation.");
      setOpenConfirm(true);
    } finally {
      setValidating(false);
    }
  };

  const handleConfirmOverwrite = async () => {
    if (!selectedFile) return;
    setOpenConfirm(false);
    await uploadScenarioFile(fileKey, selectedFile);
  };

  const onPreview = async () => {
    if (selectedScenario) await fetchScenarioData(selectedScenario, fileKey);
    setOpenPreview(true);
  };

  return (
    <div className="rounded-xl border border-border bg-card p-4 shadow-elevated flex flex-col gap-3">
      <div className="flex items-start gap-3">
        <div
          className={
            "size-9 shrink-0 rounded-lg grid place-items-center " +
            (present ? "bg-positive/15 text-positive" : "bg-destructive/15 text-destructive")
          }
        >
          {present ? <Check className="size-4" /> : <CircleAlert className="size-4" />}
        </div>
        <div className="min-w-0 flex-1">
          <div className="text-sm font-medium leading-tight flex items-center gap-2">
            {label}
            {validating && <Loader2 className="size-3 animate-spin text-muted-foreground" />}
          </div>
          <div className="text-[11px] text-muted-foreground mt-0.5 line-clamp-2">{description}</div>
          <div className="mt-2 flex items-center justify-between text-[10px] text-muted-foreground/70">
            <span className="font-mono">{fileKey}</span>
            <a
              href={`/api/templates/${fileKey}`}
              download={`${fileKey}_template.xlsx`}
              className="underline hover:text-primary transition-colors cursor-pointer flex items-center gap-1 font-medium text-primary/80"
            >
              <Download className="size-3" /> Template
            </a>
          </div>
        </div>
      </div>
      <div className="flex items-center gap-2 mt-auto">
        <Button size="sm" variant="outline" className="flex-1 cursor-pointer" onClick={onChoose} disabled={validating}>
          <Upload className="size-3.5" /> Upload
        </Button>
        <Button size="sm" variant="ghost" className="cursor-pointer" onClick={onPreview} disabled={!present}>
          <Eye className="size-3.5" /> Preview
        </Button>
        <input
          ref={inputRef}
          type="file"
          accept=".csv"
          className="hidden"
          onChange={(e) => handleFileChange(e.target.files?.[0] ?? null)}
        />
      </div>

      {/* Confirmation & Validation Result Dialog */}
      <Dialog open={openConfirm} onOpenChange={setOpenConfirm}>
        <DialogContent className="max-w-xl">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              {validationError ? "Validation Rejection" : "Confirm Overwrite / Upload"}
            </DialogTitle>
            <DialogDescription>
              {validationError 
                ? "The selected file could not be uploaded due to validation errors." 
                : `Review changes for ${label} before applying them to the active scenario.`}
            </DialogDescription>
          </DialogHeader>

          {validationError ? (
            <div className="space-y-4 py-2">
              <div className="p-3 bg-destructive/10 border border-destructive/20 rounded-lg text-sm text-destructive flex items-start gap-2">
                <CircleAlert className="size-4 shrink-0 mt-0.5" />
                <span className="font-medium whitespace-pre-wrap">{validationError}</span>
              </div>
              <div className="flex justify-end">
                <Button variant="outline" className="cursor-pointer" onClick={() => setOpenConfirm(false)}>
                  Close
                </Button>
              </div>
            </div>
          ) : (
            diffResult && (
              <div className="space-y-4 py-2 max-h-[60vh] overflow-y-auto pr-1">
                {/* Structure Diff Logs */}
                {diffResult.diff && diffResult.diff.length > 0 && (
                  <div className="bg-muted/40 border rounded-lg p-3 space-y-1.5">
                    <div className="text-[11px] uppercase tracking-wider text-muted-foreground font-semibold">
                      Structural File Changes
                    </div>
                    <ul className="text-xs space-y-1 text-foreground/80 list-disc list-inside">
                      {diffResult.diff.map((log: string, idx: number) => (
                        <li key={idx}>{log}</li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Specific volume diff */}
                {diffResult.volume_delta_by_material && diffResult.volume_delta_by_material.length > 0 && (
                  <div className="space-y-1.5">
                    <div className="text-[11px] uppercase tracking-wider text-muted-foreground font-semibold">
                      Volume Deltas by Material (MT)
                    </div>
                    <div className="border rounded overflow-hidden">
                      <table className="w-full text-xs text-left">
                        <thead className="bg-muted/50 border-b">
                          <tr>
                            <th className="px-3 py-1.5 font-medium">Material ID</th>
                            <th className="px-3 py-1.5 font-medium text-right">Base</th>
                            <th className="px-3 py-1.5 font-medium text-right">New</th>
                            <th className="px-3 py-1.5 font-medium text-right">Delta</th>
                          </tr>
                        </thead>
                        <tbody>
                          {diffResult.volume_delta_by_material.slice(0, 10).map((v: any, idx: number) => (
                            <tr key={idx} className="border-b">
                              <td className="px-3 py-1 font-mono">{v.material_id}</td>
                              <td className="px-3 py-1 text-right font-mono">{fmtNumber(v.base_volume, 3)}</td>
                              <td className="px-3 py-1 text-right font-mono">{fmtNumber(v.new_volume, 3)}</td>
                              <td className={`px-3 py-1 text-right font-mono font-medium ${v.delta > 0 ? "text-positive" : "text-destructive"}`}>
                                {v.delta > 0 ? `+${fmtNumber(v.delta, 3)}` : fmtNumber(v.delta, 3)}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                    {diffResult.volume_delta_by_material.length > 10 && (
                      <div className="text-[11px] text-muted-foreground text-center">
                        showing first 10 of {diffResult.volume_delta_by_material.length} material deltas
                      </div>
                    )}
                  </div>
                )}

                {/* Specific price diff */}
                {diffResult.price_delta_by_material && diffResult.price_delta_by_material.length > 0 && (
                  <div className="space-y-1.5">
                    <div className="text-[11px] uppercase tracking-wider text-muted-foreground font-semibold">
                      Average Price Deltas by Material (USD)
                    </div>
                    <div className="border rounded overflow-hidden">
                      <table className="w-full text-xs text-left">
                        <thead className="bg-muted/50 border-b">
                          <tr>
                            <th className="px-3 py-1.5 font-medium">Material ID</th>
                            <th className="px-3 py-1.5 font-medium text-right">Base Avg</th>
                            <th className="px-3 py-1.5 font-medium text-right">New Avg</th>
                            <th className="px-3 py-1.5 font-medium text-right">Delta</th>
                          </tr>
                        </thead>
                        <tbody>
                          {diffResult.price_delta_by_material.slice(0, 10).map((p: any, idx: number) => (
                            <tr key={idx} className="border-b">
                              <td className="px-3 py-1 font-mono">{p.material_id}</td>
                              <td className="px-3 py-1 text-right font-mono">${fmtNumber(p.base_avg_price, 2)}</td>
                              <td className="px-3 py-1 text-right font-mono">${fmtNumber(p.new_avg_price, 2)}</td>
                              <td className={`px-3 py-1 text-right font-mono font-medium ${p.delta > 0 ? "text-positive" : "text-destructive"}`}>
                                {p.delta > 0 ? `+$${fmtNumber(p.delta, 2)}` : `-$${fmtNumber(Math.abs(p.delta), 2)}`}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}

                {/* Specific var costs diff */}
                {diffResult.var_cost_delta_by_material && diffResult.var_cost_delta_by_material.length > 0 && (
                  <div className="space-y-1.5">
                    <div className="text-[11px] uppercase tracking-wider text-muted-foreground font-semibold">
                      Average Variable Cost Deltas by Material (USD)
                    </div>
                    <div className="border rounded overflow-hidden">
                      <table className="w-full text-xs text-left">
                        <thead className="bg-muted/50 border-b">
                          <tr>
                            <th className="px-3 py-1.5 font-medium">Material ID</th>
                            <th className="px-3 py-1.5 font-medium text-right">Base Avg</th>
                            <th className="px-3 py-1.5 font-medium text-right">New Avg</th>
                            <th className="px-3 py-1.5 font-medium text-right">Delta</th>
                          </tr>
                        </thead>
                        <tbody>
                          {diffResult.var_cost_delta_by_material.slice(0, 10).map((v: any, idx: number) => (
                            <tr key={idx} className="border-b">
                              <td className="px-3 py-1 font-mono">{v.material_id}</td>
                              <td className="px-3 py-1 text-right font-mono">${fmtNumber(v.base_var_cost, 2)}</td>
                              <td className="px-3 py-1 text-right font-mono">${fmtNumber(v.new_var_cost, 2)}</td>
                              <td className={`px-3 py-1 text-right font-mono font-medium ${v.delta > 0 ? "text-positive" : "text-destructive"}`}>
                                {v.delta > 0 ? `+$${fmtNumber(v.delta, 2)}` : `-$${fmtNumber(Math.abs(v.delta), 2)}`}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}

                {/* Specific FX diff */}
                {diffResult.fx_delta_by_currency && diffResult.fx_delta_by_currency.length > 0 && (
                  <div className="space-y-1.5">
                    <div className="text-[11px] uppercase tracking-wider text-muted-foreground font-semibold">
                      Average Exchange Rate Deltas (against USD)
                    </div>
                    <div className="border rounded overflow-hidden">
                      <table className="w-full text-xs text-left">
                        <thead className="bg-muted/50 border-b">
                          <tr>
                            <th className="px-3 py-1.5 font-medium">Currency</th>
                            <th className="px-3 py-1.5 font-medium text-right">Base Avg</th>
                            <th className="px-3 py-1.5 font-medium text-right">New Avg</th>
                            <th className="px-3 py-1.5 font-medium text-right">Delta</th>
                          </tr>
                        </thead>
                        <tbody>
                          {diffResult.fx_delta_by_currency.map((fx: any, idx: number) => (
                            <tr key={idx} className="border-b">
                              <td className="px-3 py-1 font-semibold">{fx.currency}</td>
                              <td className="px-3 py-1 text-right font-mono">{fmtNumber(fx.base_rate, 4)}</td>
                              <td className="px-3 py-1 text-right font-mono">{fmtNumber(fx.new_rate, 4)}</td>
                              <td className={`px-3 py-1 text-right font-mono font-medium ${fx.delta > 0 ? "text-positive" : "text-destructive"}`}>
                                {fx.delta > 0 ? `+${fmtNumber(fx.delta, 4)}` : fmtNumber(fx.delta, 4)}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}

                {(!diffResult.diff || diffResult.diff.length === 0) && (
                  <div className="text-sm text-center py-4 text-muted-foreground">
                    No structural changes detected between the current and selected files.
                  </div>
                )}

                <div className="flex justify-end gap-2 border-t pt-4">
                  <Button variant="outline" className="cursor-pointer" onClick={() => setOpenConfirm(false)}>
                    Cancel
                  </Button>
                  <Button onClick={handleConfirmOverwrite} className="bg-gradient-brand text-white shadow-glow cursor-pointer">
                    Overwrite Scenario File
                  </Button>
                </div>
              </div>
            )
          )}
        </DialogContent>
      </Dialog>

      <Dialog open={openPreview} onOpenChange={setOpenPreview}>
        <DialogContent className="max-w-5xl">
          <DialogHeader>
            <DialogTitle>{label}</DialogTitle>
            <DialogDescription>First 100 rows · {fileKey}</DialogDescription>
          </DialogHeader>
          <div className="max-h-[60vh] overflow-auto rounded border border-border">
            {loadingData ? (
              <div className="p-10 grid place-items-center text-muted-foreground">
                <Loader2 className="size-5 animate-spin" />
              </div>
            ) : data.length === 0 ? (
              <div className="p-10 text-center text-sm text-muted-foreground">No data</div>
            ) : (
              <table className="w-full text-[12px]">
                <thead className="sticky top-0 bg-card border-b border-border">
                  <tr>
                    {Object.keys(data[0]).map((k) => (
                      <th
                        key={k}
                        className="px-3 py-2 text-left text-[11px] uppercase tracking-[0.1em] text-muted-foreground font-medium"
                      >
                        {k}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {data.map((row, i) => (
                    <tr key={i} className="border-b border-border/60">
                      {Object.keys(data[0]).map((k) => {
                        const v = row[k];
                        const isNum = typeof v === "number";
                        return (
                          <td key={k} className={"px-3 py-1.5 " + (isNum ? "text-right tabular font-mono" : "")}>
                            {v === null || v === undefined ? "—" : isNum ? fmtNumber(v, 3) : String(v)}
                          </td>
                        );
                      })}
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}

function OverridesPanel() {
  const { overrides, addOverride, removeOverride, loadingCalculation } = useAppStore();
  const [form, setForm] = useState<Override>({
    "Material ID": "",
    "Sold to ID": "",
    "Ship to ID": "",
    Date: "",
    Price: 0,
  });

  const submit = async () => {
    if (!form["Material ID"] || !form["Sold to ID"] || !form["Ship to ID"] || !form.Date || !form.Price) return;
    await addOverride({ ...form, Price: Number(form.Price) });
    setForm({ "Material ID": "", "Sold to ID": "", "Ship to ID": "", Date: "", Price: 0 });
  };

  return (
    <div className="rounded-2xl border border-border bg-card shadow-elevated">
      <div className="px-5 py-4 border-b border-border flex items-center justify-between">
        <div>
          <h3 className="text-sm font-semibold">Price overrides</h3>
          <p className="text-[12px] text-muted-foreground">
            Temporarily override prices for a material / customer / ship-to / month combination.
          </p>
        </div>
        <div className="text-[11px] uppercase tracking-[0.14em] text-muted-foreground tabular">
          {overrides.length} active
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-6 gap-3 p-5 border-b border-border bg-secondary/40">
        <div className="space-y-1.5">
          <Label className="text-[11px] uppercase tracking-wider">Material ID</Label>
          <Input
            value={form["Material ID"]}
            onChange={(e) => setForm({ ...form, "Material ID": e.target.value })}
            placeholder="M-001"
          />
        </div>
        <div className="space-y-1.5">
          <Label className="text-[11px] uppercase tracking-wider">Sold to ID</Label>
          <Input
            value={form["Sold to ID"]}
            onChange={(e) => setForm({ ...form, "Sold to ID": e.target.value })}
            placeholder="ST-100"
          />
        </div>
        <div className="space-y-1.5">
          <Label className="text-[11px] uppercase tracking-wider">Ship to ID</Label>
          <Input
            value={form["Ship to ID"]}
            onChange={(e) => setForm({ ...form, "Ship to ID": e.target.value })}
            placeholder="SH-200"
          />
        </div>
        <div className="space-y-1.5">
          <Label className="text-[11px] uppercase tracking-wider">Date (YYYY-MM)</Label>
          <Input
            value={form.Date}
            onChange={(e) => setForm({ ...form, Date: e.target.value })}
            placeholder="2026-01"
          />
        </div>
        <div className="space-y-1.5">
          <Label className="text-[11px] uppercase tracking-wider">Price</Label>
          <Input
            type="number"
            value={form.Price || ""}
            onChange={(e) => setForm({ ...form, Price: Number(e.target.value) })}
            placeholder="1250"
          />
        </div>
        <div className="flex items-end">
          <Button onClick={submit} disabled={loadingCalculation} className="w-full bg-gradient-brand text-white">
            {loadingCalculation ? <Loader2 className="size-4 animate-spin" /> : <Plus className="size-4" />} Add
          </Button>
        </div>
      </div>

      <div className="max-h-[360px] overflow-auto">
        <table className="w-full text-[12px]">
          <thead className="sticky top-0 bg-card border-b border-border">
            <tr className="text-muted-foreground uppercase tracking-[0.1em] text-[11px]">
              <th className="text-left px-4 py-2">Material ID</th>
              <th className="text-left px-4 py-2">Sold to ID</th>
              <th className="text-left px-4 py-2">Ship to ID</th>
              <th className="text-left px-4 py-2">Date</th>
              <th className="text-right px-4 py-2">Price</th>
              <th className="w-10" />
            </tr>
          </thead>
          <tbody>
            {overrides.length === 0 && (
              <tr>
                <td colSpan={6} className="text-center text-muted-foreground py-8 text-sm">
                  No overrides yet
                </td>
              </tr>
            )}
            {overrides.map((o, i) => (
              <tr key={i} className="border-b border-border/60 hover:bg-secondary/40">
                <td className="px-4 py-2 font-mono">{o["Material ID"]}</td>
                <td className="px-4 py-2 font-mono">{o["Sold to ID"]}</td>
                <td className="px-4 py-2 font-mono">{o["Ship to ID"]}</td>
                <td className="px-4 py-2 font-mono">{o.Date}</td>
                <td className="px-4 py-2 text-right tabular font-mono">{fmtNumber(o.Price, 2)}</td>
                <td className="px-2">
                  <Button size="icon" variant="ghost" onClick={() => removeOverride(i)} className="size-8">
                    <Trash2 className="size-3.5" />
                  </Button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export function ScenarioManager() {
  const { selectedScenarioMeta } = useAppStore();
  const presentCount = Object.values(selectedScenarioMeta?.files_status || {}).filter(Boolean).length;
  return (
    <div className="space-y-6">
      <div className="rounded-2xl border border-border bg-card p-6 shadow-elevated bg-aurora">
        <div className="flex flex-wrap items-end justify-between gap-3">
          <div>
            <div className="text-[11px] uppercase tracking-[0.14em] text-muted-foreground">Input files</div>
            <h2 className="mt-1 text-xl font-semibold tracking-tight">
              <span className="text-gradient-brand">{presentCount}</span>
              <span className="text-muted-foreground"> / 7 required files present</span>
            </h2>
          </div>
          <p className="text-[12px] text-muted-foreground max-w-md">
            Each scenario requires 7 input CSVs. Upload a new file to overwrite the current one — the calculation
            pipeline will re-run automatically.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-3">
        {FILE_DEFS.map((f) => (
          <FileCard key={f.key} fileKey={f.key} label={f.label} description={f.description} />
        ))}
      </div>

      <OverridesPanel />
    </div>
  );
}
