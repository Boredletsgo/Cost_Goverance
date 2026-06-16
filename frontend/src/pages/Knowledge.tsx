import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent } from "@/components/ui/card";
import { api } from "@/lib/api";
import { Search } from "lucide-react";

interface Result {
  text: string;
  metadata: Record<string, unknown>;
  score: number;
}

export function Knowledge() {
  const [q, setQ] = useState("");
  const [results, setResults] = useState<Result[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(false);

  async function search() {
    if (!q.trim()) return;
    setLoading(true);
    setSearched(true);
    try {
      const res = await api.searchKnowledge(q);
      setResults(res.results);
      setTotal(res.total_docs);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-4">
      <p className="text-sm text-muted-foreground">
        RAG-powered semantic search across infrastructure knowledge, resources, events, and findings.
      </p>
      <form onSubmit={(e) => { e.preventDefault(); search(); }} className="flex gap-2">
        <Input value={q} onChange={(e) => setQ(e.target.value)} placeholder="e.g. how to fix high database cost after deploy" />
        <Button type="submit" disabled={loading}>
          <Search size={16} /> Search
        </Button>
      </form>
      {total > 0 && <div className="text-xs text-muted-foreground">{total} documents indexed</div>}

      <div className="space-y-2">
        {results.map((r, i) => (
          <Card key={i}>
            <CardContent className="py-3">
              <div className="flex items-center justify-between mb-1">
                <span className="text-[10px] uppercase tracking-wide text-muted-foreground">
                  {String(r.metadata.kind || r.metadata.topic || "knowledge")}
                  {r.metadata.connector ? ` · ${r.metadata.connector}` : ""}
                </span>
                <span className="text-xs text-primary">{Math.round(r.score * 100)}% match</span>
              </div>
              <p className="text-sm leading-relaxed">{r.text}</p>
            </CardContent>
          </Card>
        ))}
        {searched && !loading && results.length === 0 && (
          <div className="text-sm text-muted-foreground">No matches found.</div>
        )}
      </div>
    </div>
  );
}
