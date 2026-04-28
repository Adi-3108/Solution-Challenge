import { MetricResult } from "@/types/api";
import { formatMetricValue } from "@/utils/format";
import { Card } from "@/components/Common/Card";
import { StatusBadge } from "@/components/Common/StatusBadge";

export const BiasScorecard = ({ metrics }: { metrics: MetricResult[] }) => (
  <div className="grid gap-4 lg:grid-cols-2 xl:grid-cols-3">
    {metrics.map((metric) => (
      <Card key={`${metric.metric_name}-${metric.group_name}`} className="space-y-4">
        <div className="flex items-start justify-between gap-3">
          <div>
            <p className="text-xs uppercase tracking-wide text-slate-500 dark:text-slate-400">
              {metric.group_name}
            </p>
            <h3 className="mt-1 text-lg font-semibold text-slate-950 dark:text-white">
              {metric.display_name ?? metric.metric_name}
            </h3>
          </div>
          <StatusBadge severity={metric.severity} />
        </div>
        <div className="space-y-2">
          <p className="font-mono text-2xl font-bold text-slate-950 dark:text-white">
            {formatMetricValue(metric.metric_name, metric.value)}
          </p>
          <p className="text-xs text-slate-500 dark:text-slate-400">
            Threshold: {metric.threshold_used}
          </p>
        </div>
        <details className="rounded-xl bg-slate-50 p-3 text-sm text-slate-600 dark:bg-slate-900/60 dark:text-slate-300">
          <summary className="cursor-pointer font-medium text-slate-800 dark:text-slate-100">
            Plain-English explanation
          </summary>
          <p className="mt-3 leading-6">{metric.explanation}</p>
        </details>
      </Card>
    ))}
  </div>
);

