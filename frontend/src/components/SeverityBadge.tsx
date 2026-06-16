import { Badge } from "@/components/ui/badge";
import { severityColor } from "@/lib/utils";

export function SeverityBadge({ severity }: { severity: string }) {
  return (
    <Badge className={severityColor[severity] || severityColor.info}>
      {severity}
    </Badge>
  );
}
