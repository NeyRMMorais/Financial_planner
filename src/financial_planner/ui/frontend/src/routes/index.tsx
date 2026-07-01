import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { Sidebar, type ViewKey } from "@/components/app/Sidebar";
import { TopBar } from "@/components/app/TopBar";
import { Dashboard } from "@/components/app/Dashboard";
import { ScenarioManager } from "@/components/app/ScenarioManager";
import { Compare } from "@/components/app/Compare";
import { useAppStore } from "@/store/useAppStore";
import { Login } from "@/components/app/Login";
import { AdminPanel } from "@/components/app/AdminPanel";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "Financial Planner" },
      {
        name: "description",
        content:
          "Corporate FP&A planning dashboard: scenarios, calculated revenue/VCM tables, file uploads, and side-by-side variance comparison.",
      },
      { property: "og:title", content: "Financial Planner" },
      {
        property: "og:description",
        content: "Premium FP&A planning workspace with scenario management, calculation pipeline and variance analysis.",
      },
    ],
  }),
  component: AppPage,
});

const TITLES: Record<ViewKey, { title: string; subtitle: string }> = {
  dashboard: { title: "Dashboard", subtitle: "Calculated results for the active scenario" },
  manager: { title: "Scenario Manager", subtitle: "Input files, validation, and price overrides" },
  compare: { title: "Compare", subtitle: "Variance analysis across two scenarios" },
  admin: { title: "Admin Panel", subtitle: "Review corporate application login audit trails" },
};

function AppPage() {
  const [view, setView] = useState<ViewKey>("dashboard");
  const [dark, setDark] = useState(true);
  const user = useAppStore((s) => s.user);
  const fetchScenarios = useAppStore((s) => s.fetchScenarios);

  useEffect(() => {
    if (user) {
      fetchScenarios();
    }
  }, [fetchScenarios, user]);

  useEffect(() => {
    document.documentElement.classList.toggle("dark", dark);
  }, [dark]);

  if (!user) {
    return <Login />;
  }

  return (
    <div className="flex min-h-screen bg-background text-foreground">
      <Sidebar view={view} onView={setView} dark={dark} />
      <div className="flex-1 min-w-0 flex flex-col">
        <TopBar title={TITLES[view].title} subtitle={TITLES[view].subtitle} dark={dark} onToggleDark={() => setDark((d) => !d)} />
        <main className="flex-1 p-6 lg:p-8 max-w-[1600px] w-full mx-auto">
          {view === "dashboard" && <Dashboard />}
          {view === "manager" && <ScenarioManager />}
          {view === "compare" && <Compare />}
          {view === "admin" && <AdminPanel />}
        </main>
      </div>
    </div>
  );
}

