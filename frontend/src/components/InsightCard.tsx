import { Card, CardContent } from "@/components/ui/card";
import { SeverityBadge } from "./SeverityBadge";
import { currency } from "@/lib/utils";
import type { Insight } from "@/lib/api";

const agentLabel: Record<string, string> = {
  cost: "Cost Intelligence",
  incident: "Incident Intelligence",
  security: "Security Intelligence",
  optimization: "Optimization",
  executive: "Executive",
};

export function InsightCard({ insight }: { insight: Insight }) {
  return (
    <Card className="hover:border-primary/50 transition-colors">
      <CardContent className="pt-4">
        <div className="flex items-start justify-between gap-3">
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-1">
              <SeverityBadge severity={insight.severity} />
              <span className="text-xs text-muted-foreground uppercase tracking-wide">
                {agentLabel[insight.agent] || insight.agent} · {insight.kind}
              </span>
            </div>
            <h4 className="font-medium text-sm">{insight.title}</h4>
            <p className="text-sm text-muted-foreground mt-1 leading-relaxed">
              {insight.summary}
            </p>
          </div>
          {insight.impact_usd > 0 && (
            <div className="text-right shrink-0">
              <div className="text-emerald-400 font-semibold">
                {currency(insight.impact_usd)}
              </div>
              <div className="text-[10px] text-muted-foreground">impact / mo</div>
            </div>
          )}
        </div>
        {insight.confidence > 0 && (
          <div className="mt-3 flex items-center gap-2">
            <div className="h-1 flex-1 rounded-full bg-muted overflow-hidden">
              <div
                className="h-full bg-primary"
                style={{ width: `${Math.round(insight.confidence * 100)}%` }}
              />
            </div>
            <span className="text-[10px] text-muted-foreground">
              {Math.round(insight.confidence * 100)}% confidence
            </span>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
