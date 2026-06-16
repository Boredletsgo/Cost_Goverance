const BASE = (import.meta.env.VITE_API_BASE_URL as string) || "http://localhost:8000";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}/api${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`${res.status}: ${text}`);
  }
  return res.json() as Promise<T>;
}

export interface Insight {
  id: string;
  agent: string;
  kind: string;
  title: string;
  summary: string;
  severity: string;
  confidence: number;
  impact_usd: number;
  details: Record<string, unknown>;
  status: string;
  created_at: string;
}

export interface DashboardSummary {
  total_monthly_cost: number;
  cost_trend_pct: number;
  open_incidents: number;
  critical_findings: number;
  active_insights: number;
  potential_savings_usd: number;
  resources_by_connector: Record<string, number>;
  cost_by_service: { service: string; connector: string; amount: number }[];
  cost_timeseries: { date: string; amount: number }[];
  recent_insights: Insight[];
}

export interface ChatResponse {
  conversation_id: string;
  agent: string;
  answer: string;
  citations: { text: string; metadata: Record<string, unknown>; score: number }[];
  insights: Insight[];
  trace: { step: string; agent?: string }[];
}

export interface ConnectorInfo {
  name: string;
  enabled: boolean;
  capabilities: string[];
  description: string;
}

export interface ConnectorSetupStatus {
  name: string;
  enabled: boolean;
  capabilities: string[];
  description: string;
  mode: string;
  requested_mode: string;
  has_live: boolean;
  sdk_available: boolean;
  credentials_detected: boolean;
}

export interface TestResult {
  ok: boolean;
  detail: string;
}

export interface AgentInfo {
  name: string;
  title: string;
  description: string;
}

export const api = {
  dashboard: () => request<DashboardSummary>("/dashboard"),
  health: () => request<{ status: string; llm_provider: string; knowledge_docs: number }>("/health"),
  chat: (message: string, agent?: string, conversation_id?: string) =>
    request<ChatResponse>("/chat", {
      method: "POST",
      body: JSON.stringify({ message, agent, conversation_id }),
    }),
  agents: () => request<AgentInfo[]>("/agents"),
  runSweep: () => request<Insight[]>("/agents/sweep", { method: "POST" }),
  insights: (params?: Record<string, string>) => {
    const qs = params ? "?" + new URLSearchParams(params).toString() : "";
    return request<Insight[]>(`/insights${qs}`);
  },
  connectors: () => request<ConnectorInfo[]>("/connectors"),
  refreshConnectors: () => request<{ status: string }>("/connectors/refresh", { method: "POST" }),
  setupStatus: () => request<{ connectors: ConnectorSetupStatus[] }>("/setup/status"),
  setConnectorMode: (name: string, mode: string) =>
    request<ConnectorSetupStatus>(`/setup/connectors/${name}/mode`, {
      method: "POST",
      body: JSON.stringify({ mode }),
    }),
  testConnector: (name: string) =>
    request<TestResult>(`/setup/connectors/${name}/test`, { method: "POST" }),
  searchKnowledge: (q: string) =>
    request<{ query: string; results: { text: string; metadata: Record<string, unknown>; score: number }[]; total_docs: number }>(
      `/knowledge/search?q=${encodeURIComponent(q)}`
    ),
  generateReport: () => request<{ id: string; title: string; body_html: string }>("/reports/generate", { method: "POST" }),
};
