import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useParams } from "react-router-dom";

import { HeatmapDatum, HeatmapChart } from "@/components/Charts/HeatmapChart";
import { CounterfactualPanel } from "@/components/Runs/CounterfactualPanel";
import { DriftPanel } from "@/components/Runs/DriftPanel";
import { HistoricalComparison } from "@/components/Runs/HistoricalComparison";
import { LineMetricChart } from "@/components/Charts/LineMetricChart";
import { OutcomeBarChart } from "@/components/Charts/OutcomeBarChart";
import { RiskGauge } from "@/components/Charts/RiskGauge";
import { AuditProgress } from "@/components/Runs/AuditProgress";
import { BiasScorecard } from "@/components/Runs/BiasScorecard";
import { Card } from "@/components/Common/Card";
import { PageHeader } from "@/components/Common/PageHeader";
import { RemediationCard } from "@/components/Runs/RemediationCard";
import { ReportPanel } from "@/components/Runs/ReportPanel";
import { useRunPolling } from "@/hooks/useRunPolling";
import { runsService } from "@/services/runs.service";

const tabs = [
  "overview",
  "distributions",
  "model",
  "counterfactual",
  "drift",
  "proxy",
  "remediation",
  "report",
] as const;

const tabLabels: Record<(typeof tabs)[number], string> = {
  overview: "Overview",
  distributions: "Distributions",
  model: "Model fairness",
  counterfactual: "Counterfactual",
  drift: "Drift",
  proxy: "Proxy",
  remediation: "Remediation",
  report: "Report",
};

export const RunDetailPage = () => {
  const { runId = "" } = useParams();
  const [activeTab, setActiveTab] = useState<(typeof tabs)[number]>("overview");
  const runQuery = useRunPolling(runId);
  const resultsQuery = useQuery({
    queryKey: ["run-results", runId],
    queryFn: () => runsService.results(runId),
    enabled: runQuery.data?.status === "completed",
  });

  const results = resultsQuery.data;
  const topIssues = useMemo(
    () =>
      results?.metrics
        .filter((metric) => metric.severity !== "green")
        .slice()
        .sort((left, right) => Math.abs(right.value) - Math.abs(left.value))
        .slice(0, 3) ?? [],
    [results?.metrics],
  );

  const proxyHeatmapData = useMemo<HeatmapDatum[]>(() => {
    const proxyEntries = Object.entries(results?.proxy.matrix ?? {});
    return proxyEntries.flatMap(([feature, groups], featureIndex) =>
      Object.entries(groups).map(([group, value], groupIndex) => ({
        x: groupIndex + 1,
        y: featureIndex + 1,
        z: value,
        xLabel: group,
        yLabel: feature,
      })),
    );
  }, [results?.proxy.matrix]);

  const intersectionalHeatmapData = useMemo<HeatmapDatum[]>(() => {
    const intersections = results?.distributions.intersectionality ?? [];
    return intersections.map((metric, index) => {
      const labels = Object.values(metric.intersectional_groups ?? {});
      return {
        x: (index % 4) + 1,
        y: Math.floor(index / 4) + 1,
        z: Math.abs(metric.value),
        xLabel: labels[0] ?? metric.group_name,
        yLabel: labels[1] ?? "Intersection",
      };
    });
  }, [results?.distributions.intersectionality]);

  if (!runQuery.data) {
    return <div className="panel p-6">Loading run...</div>;
  }

  return (
    <div className="space-y-8">
      <PageHeader
        title="Audit run"
        subtitle="Review fairness metrics, proxy-variable risks, model behavior, and recommended mitigations for this audit."
      />
      <AuditProgress run={runQuery.data} />

      {runQuery.data.status !== "completed" || !results ? (
        <Card className="space-y-2">
          <h2 className="text-lg font-semibold text-slate-950 dark:text-white">Run in progress</h2>
          <p className="text-sm text-slate-600 dark:text-slate-300">{runQuery.data.stage_label}</p>
        </Card>
      ) : (
        <div className="grid gap-6 lg:grid-cols-[220px_1fr]">
          <aside className="panel sticky top-28 flex h-fit flex-col gap-2 p-4">
            {tabs.map((tab) => (
              <button
                key={tab}
                type="button"
                onClick={() => setActiveTab(tab)}
                className={`rounded-lg px-3 py-2 text-left font-medium ${
                  activeTab === tab
                    ? "bg-brand-600 text-white"
                    : "text-slate-600 hover:bg-slate-100 dark:text-slate-200 dark:hover:bg-slate-700"
                }`}
              >
                {tabLabels[tab]}
              </button>
            ))}
          </aside>

          <div className="space-y-6">
            {activeTab === "overview" && (
              <>
                <section className="grid gap-6 xl:grid-cols-[0.75fr_1.25fr]">
                  <RiskGauge score={runQuery.data.bias_risk_score} />
                  <Card className="space-y-4">
                    <h2 className="text-lg font-semibold text-slate-950 dark:text-white">
                      Top critical issues
                    </h2>
                    <div className="space-y-3">
                      {topIssues.map((metric) => (
                        <div key={`${metric.metric_name}-${metric.group_name}`} className="rounded-xl bg-slate-50 p-4 dark:bg-slate-900/60">
                          <p className="font-semibold text-slate-950 dark:text-white">
                            {metric.display_name ?? metric.metric_name}
                          </p>
                          <p className="text-sm text-slate-600 dark:text-slate-300">
                            {metric.explanation}
                          </p>
                        </div>
                      ))}
                    </div>
                  </Card>
                </section>
                <BiasScorecard metrics={results.metrics} />
                <HistoricalComparison history={results.drift.risk_history} />
              </>
            )}

            {activeTab === "distributions" && (
              <>
                {results.distributions.distributions.map((distribution) => (
                  <OutcomeBarChart
                    key={distribution.protected_attribute}
                    title={`Outcome rates by ${distribution.protected_attribute}`}
                    description="Compare positive outcome rates side by side for each protected group."
                    summary={`Chart compares positive outcome rates across ${distribution.protected_attribute}.`}
                    data={distribution.groups}
                  />
                ))}
                <HeatmapChart
                  title="Intersectionality heatmap"
                  description="Surfaces high-risk intersections where single-attribute analysis can miss harm."
                  summary="Intersectionality heatmap showing risk severity at protected group intersections."
                  data={intersectionalHeatmapData}
                />
              </>
            )}

            {activeTab === "model" && (
              <>
                <LineMetricChart
                  title="Calibration curves"
                  description="Compare predicted confidence against observed positive rates by group."
                  summary="Calibration chart compares mean score against positive rate."
                  data={Object.entries(results.distributions.calibration_curves).flatMap(([group, values]) =>
                    values.map((value, index) => ({
                      bucket: `${group}-${index + 1}`,
                      mean_score: value.mean_score,
                      positive_rate: value.positive_rate,
                    })),
                  )}
                  xKey="bucket"
                  lines={[
                    { key: "mean_score", label: "Mean score" },
                    { key: "positive_rate", label: "Observed positive rate" },
                  ]}
                />
                <LineMetricChart
                  title="ROC curves"
                  description="Compare false-positive and true-positive tradeoffs across groups."
                  summary="ROC chart compares group curves."
                  data={Object.entries(results.distributions.roc_curves).flatMap(([group, points]) =>
                    points.map((point, index) => ({
                      point: `${group}-${index + 1}`,
                      fpr: point.fpr,
                      tpr: point.tpr,
                    })),
                  )}
                  xKey="point"
                  lines={[
                    { key: "fpr", label: "False positive rate" },
                    { key: "tpr", label: "True positive rate" },
                  ]}
                />
              </>
            )}

            {activeTab === "counterfactual" && (
              <CounterfactualPanel assessments={results.counterfactual} />
            )}

            {activeTab === "drift" && <DriftPanel drift={results.drift} />}

            {activeTab === "proxy" && (
              <HeatmapChart
                title="Proxy variable heatmap"
                description="Highlights non-protected variables that correlate strongly with protected attributes."
                summary="Correlation heatmap for proxy-variable detection."
                data={proxyHeatmapData}
              />
            )}

            {activeTab === "remediation" && (
              <div className="space-y-6">
                {results.recommendations.map((recommendation) => (
                  <RemediationCard key={`${recommendation.metric_name}-${recommendation.title}`} recommendation={recommendation} />
                ))}
              </div>
            )}

            {activeTab === "report" && <ReportPanel runId={runId} />}
          </div>
        </div>
      )}
    </div>
  );
};
