import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { api, type ConnectorInfo } from "@/lib/api";
import { Cloud, RefreshCw, CheckCircle2, Circle } from "lucide-react";

export function Connectors() {
  const [connectors, setConnectors] = useState<ConnectorInfo[]>([]);
  const [loading, setLoading] = useState(false);
  const [msg, setMsg] = useState("");

  useEffect(() => {
    api.connectors().then(setConnectors).catch(() => {});
  }, []);

  async function refresh() {
    setLoading(true);
    setMsg("");
    try {
      await api.refreshConnectors();
      setMsg("Connector data refreshed and re-indexed.");
    } catch (e) {
      setMsg(`Error: ${String(e)}`);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <p className="text-sm text-muted-foreground">
          Plug-and-play connectors implementing the universal <code className="text-primary">BaseConnector</code> interface.
        </p>
        <Button size="sm" variant="secondary" onClick={refresh} disabled={loading}>
          <RefreshCw size={14} className={loading ? "animate-spin" : ""} /> Refresh data
        </Button>
      </div>
      {msg && <div className="text-xs text-emerald-400">{msg}</div>}

      <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-3">
        {connectors.map((c) => (
          <Card key={c.name}>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="flex items-center gap-2 text-foreground capitalize">
                  <Cloud size={16} className="text-primary" /> {c.name}
                </CardTitle>
                {c.enabled ? (
                  <span className="flex items-center gap-1 text-xs text-emerald-400">
                    <CheckCircle2 size={12} /> enabled
                  </span>
                ) : (
                  <span className="flex items-center gap-1 text-xs text-muted-foreground">
                    <Circle size={12} /> disabled
                  </span>
                )}
              </div>
            </CardHeader>
            <CardContent>
              <p className="text-xs text-muted-foreground mb-3">{c.description}</p>
              <div className="flex flex-wrap gap-1">
                {c.capabilities.map((cap) => (
                  <Badge key={cap} className="border-border bg-muted text-muted-foreground">
                    {cap}
                  </Badge>
                ))}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
