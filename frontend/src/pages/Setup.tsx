import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { api, type ConnectorSetupStatus, type TestResult } from "@/lib/api";
import {
  Plug,
  RefreshCw,
  CheckCircle2,
  XCircle,
  KeyRound,
  PackageCheck,
  PackageX,
  FlaskConical,
  Cloud,
} from "lucide-react";

type TestState = Record<string, { loading: boolean; result?: TestResult }>;

export function Setup() {
  const [items, setItems] = useState<ConnectorSetupStatus[]>([]);
  const [busy, setBusy] = useState<string | null>(null);
  const [tests, setTests] = useState<TestState>({});
  const [refreshing, setRefreshing] = useState(false);
  const [msg, setMsg] = useState("");

  function load() {
    api.setupStatus().then((r) => setItems(r.connectors)).catch(() => {});
  }
  useEffect(load, []);

  async function changeMode(name: string, mode: string) {
    setBusy(name);
    setMsg("");
    try {
      const updated = await api.setConnectorMode(name, mode);
      setItems((prev) => prev.map((c) => (c.name === name ? updated : c)));
    } catch (e) {
      setMsg(`Error: ${String(e)}`);
    } finally {
      setBusy(null);
    }
  }

  async function test(name: string) {
    setTests((p) => ({ ...p, [name]: { loading: true } }));
    try {
      const result = await api.testConnector(name);
      setTests((p) => ({ ...p, [name]: { loading: false, result } }));
    } catch (e) {
      setTests((p) => ({ ...p, [name]: { loading: false, result: { ok: false, detail: String(e) } } }));
    }
  }

  async function reingest() {
    setRefreshing(true);
    setMsg("");
    try {
      await api.refreshConnectors();
      setMsg("Data re-ingested from connectors using their current modes.");
    } catch (e) {
      setMsg(`Error: ${String(e)}`);
    } finally {
      setRefreshing(false);
    }
  }

  return (
    <div className="space-y-5">
      <div className="flex items-start justify-between gap-4">
        <p className="text-sm text-muted-foreground max-w-2xl">
          Point InfraMind at <span className="text-foreground">your own cloud</span>. Each connector runs in{" "}
          <code className="text-primary">mock</code> mode (bundled sample data, zero config) or{" "}
          <code className="text-primary">live</code> mode (real AWS/Azure APIs). Switch to live, test the connection, then
          re-ingest. Credentials are read from your environment only — never stored by the app.
        </p>
        <Button size="sm" variant="secondary" onClick={reingest} disabled={refreshing}>
          <RefreshCw size={14} className={refreshing ? "animate-spin" : ""} /> Re-ingest data
        </Button>
      </div>
      {msg && <div className="text-xs text-emerald-400">{msg}</div>}

      <div className="grid md:grid-cols-2 gap-3">
        {items.map((c) => {
          const t = tests[c.name];
          const isLive = c.mode === "live";
          const wantsLiveButDowngraded = c.requested_mode === "live" && c.mode !== "live";
          return (
            <Card key={c.name}>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="flex items-center gap-2 text-foreground capitalize">
                    <Cloud size={16} className="text-primary" /> {c.name}
                  </CardTitle>
                  <Badge
                    className={
                      isLive
                        ? "border-emerald-500/40 bg-emerald-500/10 text-emerald-400"
                        : "border-border bg-muted text-muted-foreground"
                    }
                  >
                    {isLive ? "live" : "mock"}
                  </Badge>
                </div>
              </CardHeader>
              <CardContent className="space-y-3">
                <p className="text-xs text-muted-foreground">{c.description}</p>

                {/* mode toggle */}
                <div className="flex items-center gap-2">
                  <div className="inline-flex rounded-md border border-border overflow-hidden text-xs">
                    {["mock", "live"].map((m) => (
                      <button
                        key={m}
                        disabled={busy === c.name || (m === "live" && !c.has_live)}
                        onClick={() => changeMode(c.name, m)}
                        className={
                          "px-3 py-1.5 transition-colors disabled:opacity-40 " +
                          (c.requested_mode === m
                            ? "bg-primary text-primary-foreground"
                            : "text-muted-foreground hover:bg-muted")
                        }
                      >
                        {m}
                      </button>
                    ))}
                  </div>
                  {!c.has_live && <span className="text-[11px] text-muted-foreground">live not available yet</span>}
                </div>

                {wantsLiveButDowngraded && (
                  <div className="text-[11px] text-amber-400">
                    Requested live but running mock — install cloud SDKs (requirements-cloud.txt).
                  </div>
                )}

                {/* status chips */}
                {c.has_live && (
                  <div className="flex flex-wrap gap-2 text-[11px]">
                    <span className="inline-flex items-center gap-1 text-muted-foreground">
                      {c.sdk_available ? (
                        <PackageCheck size={12} className="text-emerald-400" />
                      ) : (
                        <PackageX size={12} className="text-muted-foreground" />
                      )}
                      SDK {c.sdk_available ? "installed" : "missing"}
                    </span>
                    <span className="inline-flex items-center gap-1 text-muted-foreground">
                      <KeyRound size={12} className={c.credentials_detected ? "text-emerald-400" : "text-amber-400"} />
                      credentials {c.credentials_detected ? "detected" : "not set"}
                    </span>
                  </div>
                )}

                <div className="flex flex-wrap gap-1">
                  {c.capabilities.map((cap) => (
                    <Badge key={cap} className="border-border bg-muted text-muted-foreground">
                      {cap}
                    </Badge>
                  ))}
                </div>

                {/* test connection */}
                {c.has_live && (
                  <div className="space-y-2">
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => test(c.name)}
                      disabled={t?.loading}
                    >
                      <FlaskConical size={14} className={t?.loading ? "animate-pulse" : ""} /> Test connection
                    </Button>
                    {t?.result && (
                      <div
                        className={
                          "flex items-start gap-1.5 text-[11px] " +
                          (t.result.ok ? "text-emerald-400" : "text-red-400")
                        }
                      >
                        {t.result.ok ? <CheckCircle2 size={12} /> : <XCircle size={12} />}
                        <span className="break-all">{t.result.detail}</span>
                      </div>
                    )}
                  </div>
                )}
              </CardContent>
            </Card>
          );
        })}
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-sm text-foreground">
            <Plug size={15} className="text-primary" /> How to go live
          </CardTitle>
        </CardHeader>
        <CardContent className="text-xs text-muted-foreground space-y-1.5">
          <div>1. Install cloud SDKs: <code className="text-primary">pip install -r requirements.txt -r requirements-cloud.txt</code></div>
          <div>2. Authenticate: <code className="text-primary">az login</code> (Azure) or <code className="text-primary">aws configure</code> (AWS), or set keys in <code className="text-primary">.env</code>.</div>
          <div>3. Set <code className="text-primary">AZURE_SUBSCRIPTION_ID</code> / <code className="text-primary">AWS_REGION</code> in <code className="text-primary">.env</code>.</div>
          <div>4. Switch the connector to <span className="text-foreground">live</span> above, hit <span className="text-foreground">Test connection</span>, then <span className="text-foreground">Re-ingest data</span>.</div>
          <div className="pt-1">See <code className="text-primary">docs/SETUP.md</code> for required permissions.</div>
        </CardContent>
      </Card>
    </div>
  );
}
