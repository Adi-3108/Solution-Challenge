import { useMutation } from "@tanstack/react-query";

import { Button } from "@/components/Common/Button";
import { Card } from "@/components/Common/Card";
import { runsService } from "@/services/runs.service";

export const ReportPanel = ({ runId }: { runId: string }) => {
  const pdfMutation = useMutation({
    mutationFn: () => runsService.generateReport(runId, "pdf"),
    onSuccess: () => {
      window.open(runsService.reportDownloadUrl(runId, "pdf"), "_blank", "noopener,noreferrer");
    },
  });

  const jsonMutation = useMutation({
    mutationFn: () => runsService.generateReport(runId, "json"),
    onSuccess: () => {
      window.open(runsService.reportDownloadUrl(runId, "json"), "_blank", "noopener,noreferrer");
    },
  });

  return (
    <Card className="space-y-4">
      <div>
        <h3 className="text-lg font-semibold text-slate-950 dark:text-white">Compliance exports</h3>
        <p className="text-sm text-slate-600 dark:text-slate-300">
          Generate immutable PDF and JSON artifacts that capture this run's metrics, flags, and remediation guidance.
        </p>
      </div>
      <div className="flex flex-wrap gap-3">
        <Button type="button" onClick={() => pdfMutation.mutate()} disabled={pdfMutation.isPending}>
          {pdfMutation.isPending ? "Generating PDF..." : "Generate PDF report"}
        </Button>
        <Button
          type="button"
          variant="secondary"
          onClick={() => jsonMutation.mutate()}
          disabled={jsonMutation.isPending}
        >
          {jsonMutation.isPending ? "Generating JSON..." : "Generate JSON export"}
        </Button>
      </div>
    </Card>
  );
};
