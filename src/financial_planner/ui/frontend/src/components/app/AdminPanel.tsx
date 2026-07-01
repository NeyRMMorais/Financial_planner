import { useEffect, useState } from "react";
import { useAppStore } from "@/store/useAppStore";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ShieldCheck, RefreshCw, Search, Loader2 } from "lucide-react";

interface LogEntry {
  timestamp: string;
  name: string;
  email: string;
  provider: string;
}

export function AdminPanel() {
  const user = useAppStore((s) => s.user);
  const fetchLoginLogs = useAppStore((s) => s.fetchLoginLogs);
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");

  const loadLogs = async () => {
    if (!user) return;
    setLoading(true);
    setError(null);
    try {
      const data = await fetchLoginLogs(user.email);
      setLogs(data);
    } catch (err: any) {
      setError(err.message || "Failed to load audit logs");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadLogs();
  }, [user]);

  const filteredLogs = logs.filter(
    (log) =>
      log.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      log.email.toLowerCase().includes(searchQuery.toLowerCase()) ||
      log.provider.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="space-y-6">
      {/* Banner Card */}
      <div className="rounded-2xl border border-border bg-card p-6 shadow-elevated bg-aurora">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="size-12 rounded-xl bg-primary/10 border border-primary/20 grid place-items-center text-primary shadow-glow">
              <ShieldCheck className="size-6" />
            </div>
            <div>
              <div className="text-[11px] uppercase tracking-[0.14em] text-muted-foreground">Admin Workspace</div>
              <h2 className="text-xl font-bold tracking-tight mt-0.5">User Sign-In Logs</h2>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <div className="text-right">
              <div className="text-[10px] uppercase tracking-wider text-muted-foreground">Total Sessions</div>
              <div className="text-2xl font-mono font-bold text-gradient-brand">{logs.length}</div>
            </div>
            <Button
              size="sm"
              variant="outline"
              onClick={loadLogs}
              disabled={loading}
              className="cursor-pointer"
            >
              {loading ? (
                <Loader2 className="size-4 animate-spin" />
              ) : (
                <RefreshCw className="size-4" />
              )}
              Reload
            </Button>
          </div>
        </div>
      </div>

      {/* Main Panel */}
      <div className="rounded-2xl border border-border bg-card shadow-elevated overflow-hidden">
        {/* Filter Toolbar */}
        <div className="p-4 border-b border-border bg-secondary/20 flex gap-3 items-center">
          <div className="relative flex-1 max-w-sm">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-muted-foreground" />
            <Input
              type="text"
              placeholder="Search by name, email or provider..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-9 bg-background/50"
            />
          </div>
        </div>

        {/* Content */}
        <div className="overflow-auto max-h-[60vh]">
          {loading && logs.length === 0 ? (
            <div className="p-20 grid place-items-center text-muted-foreground">
              <Loader2 className="size-6 animate-spin text-primary" />
              <span className="text-xs mt-2 font-medium">Fetching secure logs...</span>
            </div>
          ) : error ? (
            <div className="p-20 text-center text-destructive space-y-2">
              <p className="font-semibold">{error}</p>
              <Button size="sm" variant="outline" onClick={loadLogs} className="cursor-pointer">
                Try Again
              </Button>
            </div>
          ) : filteredLogs.length === 0 ? (
            <div className="p-20 text-center text-muted-foreground text-sm">
              {logs.length === 0 ? "No sign-in events recorded yet." : "No records match your search query."}
            </div>
          ) : (
            <table className="w-full text-[12px] text-left">
              <thead className="sticky top-0 bg-card border-b border-border z-10">
                <tr className="text-muted-foreground uppercase tracking-[0.1em] text-[11px] bg-secondary/45">
                  <th className="px-5 py-3 font-medium">Timestamp</th>
                  <th className="px-5 py-3 font-medium">Name</th>
                  <th className="px-5 py-3 font-medium">Email</th>
                  <th className="px-5 py-3 font-medium">Authentication Provider</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border/60">
                {filteredLogs.map((log, idx) => (
                  <tr key={idx} className="hover:bg-secondary/20 transition-colors">
                    <td className="px-5 py-3 font-mono text-muted-foreground">{log.timestamp}</td>
                    <td className="px-5 py-3 font-semibold text-foreground">{log.name}</td>
                    <td className="px-5 py-3 font-mono text-primary/95">{log.email}</td>
                    <td className="px-5 py-3">
                      <span className="inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-[10px] font-semibold bg-primary/10 text-primary border border-primary/20 capitalize">
                        {log.provider}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </div>
  );
}
