import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { InsightCard } from "@/components/InsightCard";
import { api, type Insight } from "@/lib/api";
import { RefreshCw } from "lucide-react";

const AGENTS = [
  { name: "", label: "All" },
  { name: "cost", label: "Cost" },
  { name: "incident", label: "Incident" },
  { name: "security", label: "Security" },
  { name: "optimization", label: "Optimization" },
  { name: "executive", label: "Executive" },
];

export function Insights() {
  const [insights, setInsights] = useState<Insight[]>([]);
  const [filter, setFilter] = useState("");
  const [loading, setLoading] = useState(false);

  function load(agent: string) {
    api.insights(agent ? { agent } : undefined).then(setInsights).catch(() => {});
  }
  useEffect(() => load(filter), [filter]);

  async function sweep() {
    setLoading(true);
    try {
      await api.runSweep();
      load(filter);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between flex-wrap gap-2">
        <div className="flex gap-2 flex-wrap">
          {AGENTS.map((a) => (
            <Button key={a.name} size="sm" variant={filter === a.name ? "default" : "outline"} onClick={() => setFilter(a.name)}>
              {a.label}
            </Button>
          ))}
        </div>
        <Button size="sm" variant="secondary" onClick={sweep} disabled={loading}>
          <RefreshCw size={14} className={loading ? "animate-spin" : ""} /> Run all agents
        </Button>
      </div>

      {insights.length === 0 ? (
        <Card>
          <CardContent className="py-8 text-center text-sm text-muted-foreground">
            No insights yet. Click "Run all agents" to generate proactive analysis.
          </CardContent>
        </Card>
      ) : (
        <div className="grid md:grid-cols-2 gap-3">
          {insights.map((i, idx) => (
            <InsightCard key={i.id || idx} insight={i} />
          ))}
        </div>
      )}
    </div>
  );
}
