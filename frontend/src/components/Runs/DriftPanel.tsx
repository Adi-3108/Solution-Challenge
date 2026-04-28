import { Card } from "@/components/Common/Card";
import { StatusBadge } from "@/components/Common/StatusBadge";
import { LineMetricChart } from "@/components/Charts/LineMetricChart";
import { DriftSummary } from "@/types/api";
import { formatDate, formatMetricValue, formatSignedNumber } from "@/utils/format";

const trendLabel: Record<DriftSummary["trend_status"], string> = {
  improving: "Improving",
  stable: "Stable",
  regressing: "Regressing",
  insufficient_history: "Need more history",
};

export const DriftPanel = ({ drift }: { drift: DriftSummary }) => {
  const historyData = drift.risk_history.map((point) => ({
    run: point.label,
    risk: point.bias_risk_score,
  }));

  return (
    <div className="space-y-6">
      <section className="grid gap-6 xl:grid-cols-[0.8fr_1.2fr]">
        <Card className="space-y-4">
          <div>
            <p className="text-xs uppercase tracking-wide text-slate-500 dark:text-slate-400">
              Trend status
            </p>
            <h2 className="mt-1 text-lg font-semibold text-slate-950 dark:text-white">
              {trendLabel[drift.trend_status]}
            </h2>
            <p className="mt-2 text-sm text-slate-600 dark:text-slate-300">
              {drift.compared_completed_at
                ? `Compared with the completed audit from ${formatDate(drift.compared_completed_at)}.`
                : "Run another completed audit to unlock direct drift comparisons."}
            </p>
          </div>

          <div className="grid gap-3 sm:grid-cols-2">
            <div className="rounded-xl bg-slate-50 p-4 dark:bg-slate-900/60">
              <p className="text-xs uppercase tracking-wide text-slate-500 dark:text-slate-400">
                Risk delta
              </p>
              <p className="mt-2 text-2xl font-semibold text-slate-950 dark:text-white">
                {drift.risk_delta === null ? "N/A" : formatSignedNumber(drift.risk_delta, 1)}
              </p>
            </div>
            <div className="rounded-xl bg-slate-50 p-4 dark:bg-slate-900/60">
              <p className="text-xs uppercase tracking-wide text-slate-500 dark:text-slate-400">
                Time periods
              </p>
              <p className="mt-2 text-2xl font-semibold text-slate-950 dark:text-white">
                {drift.period_summary.length}
              </p>
            </div>
          </div>
        </Card>

        <Card className="space-y-4">
          <div>
            <h2 className="text-lg font-semibold text-slate-950 dark:text-white">Drift alerts</h2>
            <p className="mt-1 text-sm text-slate-600 dark:text-slate-300">
              Watch for fairness regressions between model versions and review periods.
            </p>
          </div>
          {drift.alerts.length > 0 ? (
            <div className="space-y-3">
              {drift.alerts.map((alert) => (
                <div
                  key={`${alert.title}-${alert.body}`}
                  className="rounded-xl bg-slate-50 p-4 dark:bg-slate-900/60"
                >
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div>
                      <p className="font-medium text-slate-900 dark:text-slate-100">
                        {alert.title}
                      </p>
                      <p className="mt-1 text-sm text-slate-600 dark:text-slate-300">
                        {alert.body}
                      </p>
                    </div>
                    <StatusBadge severity={alert.severity} />
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="rounded-xl bg-slate-50 p-4 text-sm text-slate-600 dark:bg-slate-900/60 dark:text-slate-300">
              No drift alerts yet. The project has not accumulated enough completed history to flag
              movement confidently.
            </div>
          )}
        </Card>
      </section>

      {historyData.length > 0 && (
        <LineMetricChart
          title="Bias risk over time"
          description="See how the overall bias risk score changes across completed runs and review periods."
          summary={`Drift history contains ${historyData.length} completed runs.`}
          data={historyData}
          xKey="run"
          lines={[{ key: "risk", label: "Bias risk score" }]}
        />
      )}

      <section className="grid gap-6 xl:grid-cols-[0.9fr_1.1fr]">
        <Card className="space-y-4">
          <div>
            <h2 className="text-lg font-semibold text-slate-950 dark:text-white">
              Model versions
            </h2>
            <p className="mt-1 text-sm text-slate-600 dark:text-slate-300">
              Compare average and latest risk by model artifact or dataset-only audit mode.
            </p>
          </div>
          <div className="space-y-3">
            {drift.model_versions.map((model) => (
              <div key={`${model.model_id ?? "dataset-only"}-${model.model_label}`} className="rounded-xl bg-slate-50 p-4 dark:bg-slate-900/60">
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <p className="font-medium text-slate-900 dark:text-slate-100">
                      {model.model_label}
                    </p>
                    <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
                      {model.runs} runs · latest {formatDate(model.latest_completed_at)}
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="text-xs uppercase tracking-wide text-slate-500 dark:text-slate-400">
                      Latest
                    </p>
                    <p className="text-lg font-semibold text-slate-950 dark:text-white">
                      {model.latest_risk_score.toFixed(1)}
                    </p>
                  </div>
                </div>
                <p className="mt-3 text-sm text-slate-600 dark:text-slate-300">
                  Average risk score: {model.average_risk_score.toFixed(1)}
                </p>
              </div>
            ))}
          </div>
        </Card>

        <Card className="space-y-4">
          <div>
            <h2 className="text-lg font-semibold text-slate-950 dark:text-white">
              Biggest metric shifts
            </h2>
            <p className="mt-1 text-sm text-slate-600 dark:text-slate-300">
              Compare the current run with the previous completed audit to spot worsening or
              improving fairness checks.
            </p>
          </div>
          {drift.metric_drift.length > 0 ? (
            <div className="space-y-3">
              {drift.metric_drift.map((change) => (
                <div
                  key={`${change.metric_name}-${change.group_name}-${Object.values(change.intersectional_groups).join("-")}`}
                  className="rounded-xl bg-slate-50 p-4 dark:bg-slate-900/60"
                >
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div>
                      <p className="font-medium text-slate-900 dark:text-slate-100">
                        {change.display_name}
                      </p>
                      <p className="mt-1 text-sm text-slate-600 dark:text-slate-300">
                        {change.group_name}
                      </p>
                    </div>
                    <StatusBadge severity={change.current_severity} />
                  </div>
                  <div className="mt-3 grid gap-3 sm:grid-cols-3">
                    <div>
                      <p className="text-xs uppercase tracking-wide text-slate-500 dark:text-slate-400">
                        Previous
                      </p>
                      <p className="mt-1 font-semibold text-slate-950 dark:text-white">
                        {formatMetricValue(change.metric_name, change.previous_value)}
                      </p>
                    </div>
                    <div>
                      <p className="text-xs uppercase tracking-wide text-slate-500 dark:text-slate-400">
                        Current
                      </p>
                      <p className="mt-1 font-semibold text-slate-950 dark:text-white">
                        {formatMetricValue(change.metric_name, change.current_value)}
                      </p>
                    </div>
                    <div>
                      <p className="text-xs uppercase tracking-wide text-slate-500 dark:text-slate-400">
                        Delta
                      </p>
                      <p className="mt-1 font-semibold text-slate-950 dark:text-white">
                        {formatSignedNumber(change.delta, 3)}
                      </p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="rounded-xl bg-slate-50 p-4 text-sm text-slate-600 dark:bg-slate-900/60 dark:text-slate-300">
              Metric drift will appear once this project has at least two completed audits to
              compare.
            </div>
          )}
        </Card>
      </section>
    </div>
  );
};
