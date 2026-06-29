import { useState } from "react";
import { useAppStore } from "@/store/useAppStore";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Loader2 } from "lucide-react";

export function NewScenarioDialog({ open, onOpenChange }: { open: boolean; onOpenChange: (b: boolean) => void }) {
  const { scenarios, createScenario } = useAppStore();
  const [name, setName] = useState("");
  const [base, setBase] = useState<string>("__none__");
  const [desc, setDesc] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  const submit = async () => {
    setErr(null);
    if (!name.trim()) {
      setErr("Name is required");
      return;
    }
    setSubmitting(true);
    try {
      await createScenario(name.trim(), base === "__none__" ? null : base, desc);
      setName("");
      setDesc("");
      setBase("__none__");
      onOpenChange(false);
    } catch (e: any) {
      setErr(e.message);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[480px]">
        <DialogHeader>
          <DialogTitle>Create scenario</DialogTitle>
          <DialogDescription>Set up a new planning scenario, optionally cloned from an existing one.</DialogDescription>
        </DialogHeader>
        <div className="space-y-4 py-2">
          <div className="space-y-2">
            <Label htmlFor="name">Name</Label>
            <Input id="name" value={name} onChange={(e) => setName(e.target.value)} placeholder="e.g. 2026 Plan v2" />
          </div>
          <div className="space-y-2">
            <Label>Clone from</Label>
            <Select value={base} onValueChange={setBase}>
              <SelectTrigger>
                <SelectValue placeholder="(empty scenario)" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="__none__">— empty scenario —</SelectItem>
                {scenarios.map((s) => (
                  <SelectItem key={s.name} value={s.name}>
                    {s.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-2">
            <Label htmlFor="desc">Description</Label>
            <Textarea id="desc" rows={3} value={desc} onChange={(e) => setDesc(e.target.value)} />
          </div>
          {err && (
            <div className="rounded-md border border-destructive/30 bg-destructive/10 text-destructive text-xs p-2">
              {err}
            </div>
          )}
        </div>
        <DialogFooter>
          <Button variant="ghost" onClick={() => onOpenChange(false)}>
            Cancel
          </Button>
          <Button onClick={submit} disabled={submitting} className="bg-gradient-brand text-white">
            {submitting && <Loader2 className="size-4 animate-spin" />} Create
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
