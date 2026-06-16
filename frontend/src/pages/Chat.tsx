import { useEffect, useRef, useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent } from "@/components/ui/card";
import { api, type AgentInfo, type ChatResponse } from "@/lib/api";
import { Bot, Send, User } from "lucide-react";

interface Msg {
  role: "user" | "assistant";
  content: string;
  agent?: string;
  citations?: ChatResponse["citations"];
}

const SAMPLES = [
  "Why did costs increase yesterday?",
  "What caused today's incident?",
  "Which resources are wasting money?",
  "What should be optimized right now?",
  "Give me an executive summary",
];

export function Chat() {
  const [messages, setMessages] = useState<Msg[]>([]);
  const [input, setInput] = useState("");
  const [agent, setAgent] = useState<string>("");
  const [agents, setAgents] = useState<AgentInfo[]>([]);
  const [loading, setLoading] = useState(false);
  const [conv, setConv] = useState<string | undefined>();
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    api.agents().then(setAgents).catch(() => {});
  }, []);
  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  async function send(text: string) {
    if (!text.trim() || loading) return;
    setMessages((m) => [...m, { role: "user", content: text }]);
    setInput("");
    setLoading(true);
    try {
      const res = await api.chat(text, agent || undefined, conv);
      setConv(res.conversation_id);
      setMessages((m) => [
        ...m,
        { role: "assistant", content: res.answer, agent: res.agent, citations: res.citations },
      ]);
    } catch (e) {
      setMessages((m) => [...m, { role: "assistant", content: `Error: ${String(e)}` }]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex flex-col h-[calc(100vh-9rem)]">
      <div className="flex items-center gap-2 mb-3 flex-wrap">
        <span className="text-xs text-muted-foreground">Route to:</span>
        <Button size="sm" variant={agent === "" ? "default" : "outline"} onClick={() => setAgent("")}>
          Auto
        </Button>
        {agents.map((a) => (
          <Button key={a.name} size="sm" variant={agent === a.name ? "default" : "outline"} onClick={() => setAgent(a.name)}>
            {a.title.replace(" Intelligence Agent", "").replace(" Agent", "")}
          </Button>
        ))}
      </div>

      <div className="flex-1 overflow-y-auto space-y-4 pr-2">
        {messages.length === 0 && (
          <div className="space-y-3">
            <p className="text-sm text-muted-foreground">Ask InfraMind anything about your infrastructure:</p>
            <div className="flex flex-wrap gap-2">
              {SAMPLES.map((s) => (
                <button key={s} onClick={() => send(s)} className="text-xs px-3 py-1.5 rounded-full border border-border hover:bg-muted transition-colors">
                  {s}
                </button>
              ))}
            </div>
          </div>
        )}
        {messages.map((m, i) => (
          <div key={i} className={`flex gap-3 ${m.role === "user" ? "justify-end" : ""}`}>
            {m.role === "assistant" && (
              <div className="h-8 w-8 rounded-full bg-primary/20 flex items-center justify-center shrink-0">
                <Bot size={16} className="text-primary" />
              </div>
            )}
            <div className={`max-w-[75%] ${m.role === "user" ? "order-1" : ""}`}>
              {m.agent && <div className="text-[10px] text-muted-foreground mb-1 uppercase tracking-wide">{m.agent} agent</div>}
              <Card className={m.role === "user" ? "bg-primary/10 border-primary/30" : ""}>
                <CardContent className="py-3 text-sm whitespace-pre-wrap leading-relaxed">{m.content}</CardContent>
              </Card>
              {m.citations && m.citations.length > 0 && (
                <div className="mt-2 space-y-1">
                  <div className="text-[10px] text-muted-foreground uppercase">Sources</div>
                  {m.citations.slice(0, 3).map((c, ci) => (
                    <div key={ci} className="text-[11px] text-muted-foreground border-l-2 border-border pl-2">
                      {c.text.slice(0, 140)}… <span className="text-primary">({Math.round(c.score * 100)}%)</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
            {m.role === "user" && (
              <div className="h-8 w-8 rounded-full bg-muted flex items-center justify-center shrink-0 order-2">
                <User size={16} />
              </div>
            )}
          </div>
        ))}
        {loading && <div className="text-sm text-muted-foreground animate-pulse">Agents reasoning…</div>}
        <div ref={endRef} />
      </div>

      <form
        onSubmit={(e) => {
          e.preventDefault();
          send(input);
        }}
        className="flex gap-2 mt-4"
      >
        <Input value={input} onChange={(e) => setInput(e.target.value)} placeholder="Ask about cost, incidents, security, optimization…" />
        <Button type="submit" disabled={loading}>
          <Send size={16} />
        </Button>
      </form>
    </div>
  );
}
