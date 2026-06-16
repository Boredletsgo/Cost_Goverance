import { useEffect, useState } from "react";
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { InsightCard } from "@/components/InsightCard";
import { api, type DashboardSummary } from "@/lib/api";
import { currency } from "@/lib/utils";
import { AlertTriangle, DollarSign, Lightbulb, ShieldAlert, TrendingDown, TrendingUp } from "lucide-react";

function Stat({ label, value, icon, trend }: { label: string; value: string; icon: React.ReactNode; trend?: number }) {
  return (
    <Card>
      <CardContent className="pt-5">
        <div className="flex items-center justify-between">
          <span className="text-xs text-muted-foreground">{label}</span>
          <span className="text-primary">{icon}</span>
        </div>
        <div className="text-2xl font-semibold mt-2">{value}</div>
        {trend !== undefined && (
          <div className={`flex items-center gap-1 text-xs mt-1 ${trend >= 0 ? "text-red-400" : "text-emerald-400"}`}>
            {trend >= 0 ? <TrendingUp size={12} /> : <TrendingDown size={12} />}
            {Math.abs(trend).toFixed(1)}% vs prior period
          </div>
        )}
      </CardContent>
    </Card>
  );
}

export function Dashboard() {
  const [data, setData] = useState<DashboardSummary | null>(null);
  const [error, setError] = useState<string>("");

  useEffect(() => {
    api.dashboard().then(setData).catch((e) => setError(String(e)));
  }, []);

  if (error) return <div className="text-red-400 text-sm">Failed to load dashboard: {error}</div>;
  if (!data) return <div className="text-muted-foreground text-sm">Loading intelligence…</div>;

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-2 lg:grid-cols-5 gap-4">
        <Stat label="Projected 30-day spend" value={currency(data.total_monthly_cost)} trend={data.cost_trend_pct} icon={<DollarSign size={16} />} />
        <Stat label="Potential savings" value={currency(data.potential_savings_usd)} icon={<Lightbulb size={16} />} />
        <Stat label="Open incidents" value={String(data.open_incidents)} icon={<AlertTriangle size={16} />} />
        <Stat label="Critical findings" value={String(data.critical_findings)} icon={<ShieldAlert size={16} />} />
        <Stat label="Active insights" value={String(data.active_insights)} icon={<Lightbulb size={16} />} />
      </div>

      <div className="grid lg:grid-cols-3 gap-4">
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Daily spend trend (all connectors)</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={240}>
              <AreaChart data={data.cost_timeseries}>
                <defs>
                  <linearGradient id="g" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="hsl(245 75% 62%)" stopOpacity={0.5} />
                    <stop offset="100%" stopColor="hsl(245 75% 62%)" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="hsl(217 33% 20%)" />
                <XAxis dataKey="date" tick={{ fontSize: 11, fill: "#94a3b8" }} />
                <YAxis tick={{ fontSize: 11, fill: "#94a3b8" }} />
                <Tooltip contentStyle={{ background: "#0f172a", border: "1px solid #334155", borderRadius: 8 }} />
                <Area type="monotone" dataKey="amount" stroke="hsl(245 75% 62%)" fill="url(#g)" strokeWidth={2} />
              </AreaChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Top cost by service</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={240}>
              <BarChart data={data.cost_by_service} layout="vertical" margin={{ left: 10 }}>
                <XAxis type="number" hide />
                <YAxis type="category" dataKey="service" tick={{ fontSize: 10, fill: "#94a3b8" }} width={90} />
                <Tooltip contentStyle={{ background: "#0f172a", border: "1px solid #334155", borderRadius: 8 }} />
                <Bar dataKey="amount" fill="hsl(190 95% 50%)" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      <div>
        <h3 className="text-sm font-semibold mb-3 text-muted-foreground">Latest agent insights</h3>
        <div className="grid md:grid-cols-2 gap-3">
          {data.recent_insights.map((i, idx) => (
            <InsightCard key={i.id || idx} insight={i} />
          ))}
        </div>
      </div>
    </div>
  );
}
