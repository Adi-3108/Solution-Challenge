import { Copy } from "lucide-react";

import { Button } from "@/components/Common/Button";
import { Card } from "@/components/Common/Card";
import { LineMetricChart } from "@/components/Charts/LineMetricChart";
import { RemediationRecommendation } from "@/types/api";

export const RemediationCard = ({ recommendation }: { recommendation: RemediationRecommendation }) => (
  <Card className="space-y-4">
    <div className="flex items-start justify-between gap-4">
      <div className="space-y-1">
        <h3 className="text-lg font-semibold text-slate-950 dark:text-white">
          {recommendation.title}
        </h3>
        <p className="text-sm text-slate-600 dark:text-slate-300">{recommendation.summary}</p>
      </div>
      <Button
        type="button"
        variant="secondary"
        onClick={() => navigator.clipboard.writeText(recommendation.code_snippet)}
      >
        <Copy className="mr-2 h-4 w-4" />
        Copy code
      </Button>
    </div>
    <div className="grid gap-4 lg:grid-cols-[1.1fr_0.9fr]">
      <LineMetricChart
        title="Before and after simulation"
        description={`Recommended strategy: ${recommendation.strategy}`}
        summary={`Metric improves from ${recommendation.before_value} to ${recommendation.after_value}.`}
        data={[
          { state: "Before", value: recommendation.before_value },
          { state: "After", value: recommendation.after_value },
        ]}
        xKey="state"
        lines={[{ key: "value", label: "Metric value" }]}
      />
      <pre className="overflow-x-auto rounded-xl bg-slate-950 p-4 font-mono text-xs text-slate-100">
        <code>{recommendation.code_snippet}</code>
      </pre>
    </div>
  </Card>
);

