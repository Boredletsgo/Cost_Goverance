import { useEffect, useState } from "react";
import { Dashboard } from "./pages/Dashboard";
import { Chat } from "./pages/Chat";
import { Insights } from "./pages/Insights";
import { Connectors } from "./pages/Connectors";
import { Knowledge } from "./pages/Knowledge";
import { Reports } from "./pages/Reports";
import { api } from "./lib/api";
import { cn } from "./lib/utils";
import { Activity, Brain, Cloud, FileText, LayoutDashboard, Lightbulb, MessageSquare, Search } from "lucide-react";

const TABS = [
  { id: "dashboard", label: "Dashboard", icon: LayoutDashboard, el: <Dashboard /> },
  { id: "chat", label: "Ask InfraMind", icon: MessageSquare, el: <Chat /> },
  { id: "insights", label: "Insights", icon: Lightbulb, el: <Insights /> },
  { id: "connectors", label: "Connectors", icon: Cloud, el: <Connectors /> },
  { id: "knowledge", label: "Knowledge", icon: Search, el: <Knowledge /> },
  { id: "reports", label: "Reports", icon: FileText, el: <Reports /> },
];

export default function App() {
  const [tab, setTab] = useState("dashboard");
  const [health, setHealth] = useState<{ llm_provider: string; knowledge_docs: number } | null>(null);

  useEffect(() => {
    api.health().then(setHealth).catch(() => {});
  }, []);

  return (
    <div className="min-h-screen flex">
      <aside className="w-60 border-r border-border bg-card/50 flex flex-col shrink-0">
        <div className="p-5 flex items-center gap-2 border-b border-border">
          <div className="h-9 w-9 rounded-lg bg-primary flex items-center justify-center">
            <Brain size={20} className="text-primary-foreground" />
          </div>
          <div>
            <div className="font-semibold leading-tight">InfraMind</div>
            <div className="text-[10px] text-muted-foreground">Infrastructure Intelligence</div>
          </div>
        </div>
        <nav className="flex-1 p-3 space-y-1">
          {TABS.map((t) => {
            const Icon = t.icon;
            return (
              <button
                key={t.id}
                onClick={() => setTab(t.id)}
                className={cn(
                  "w-full flex items-center gap-3 px-3 py-2 rounded-md text-sm transition-colors",
                  tab === t.id ? "bg-primary text-primary-foreground" : "text-muted-foreground hover:bg-muted"
                )}
              >
                <Icon size={16} /> {t.label}
              </button>
            );
          })}
        </nav>
        {health && (
          <div className="p-4 border-t border-border text-[11px] text-muted-foreground space-y-1">
            <div className="flex items-center gap-2">
              <Activity size={12} className="text-emerald-400" /> LLM: <span className="text-foreground">{health.llm_provider}</span>
            </div>
            <div>{health.knowledge_docs} docs indexed</div>
          </div>
        )}
      </aside>

      <main className="flex-1 flex flex-col min-w-0">
        <header className="h-14 border-b border-border flex items-center px-6">
          <h1 className="font-semibold">{TABS.find((t) => t.id === tab)?.label}</h1>
          <span className="ml-auto text-xs text-muted-foreground">Proactive · Multi-agent · Cloud-agnostic</span>
        </header>
        <div className="flex-1 overflow-y-auto p-6">{TABS.find((t) => t.id === tab)?.el}</div>
      </main>
    </div>
  );
}
