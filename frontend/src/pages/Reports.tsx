import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { api } from "@/lib/api";
import { FileText } from "lucide-react";

export function Reports() {
  const [html, setHtml] = useState("");
  const [loading, setLoading] = useState(false);

  async function generate() {
    setLoading(true);
    try {
      const res = await api.generateReport();
      setHtml(res.body_html);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <p className="text-sm text-muted-foreground">
          The Executive Intelligence Agent compiles a weekly report (auto-emailed via Celery beat).
        </p>
        <Button size="sm" onClick={generate} disabled={loading}>
          <FileText size={14} /> Generate report now
        </Button>
      </div>
      {html ? (
        <Card>
          <CardContent className="py-4">
            <div className="bg-white rounded-md p-2 overflow-auto" dangerouslySetInnerHTML={{ __html: html }} />
          </CardContent>
        </Card>
      ) : (
        <Card>
          <CardContent className="py-8 text-center text-sm text-muted-foreground">
            No report generated yet. Click "Generate report now".
          </CardContent>
        </Card>
      )}
    </div>
  );
}
