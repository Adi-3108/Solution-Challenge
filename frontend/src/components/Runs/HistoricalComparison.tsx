import { LineMetricChart } from "@/components/Charts/LineMetricChart";
import { DriftRiskPoint } from "@/types/api";

export const HistoricalComparison = ({ history }: { history: DriftRiskPoint[] }) => {
  const chartData = history.map((point) => ({
    run: point.label,
    risk: point.bias_risk_score,
  }));

  return (
    <LineMetricChart
      title="Historical comparison"
      description="Track how the project's bias risk score moves over time across completed audits."
      summary={`Historical chart contains ${chartData.length} runs.`}
      data={chartData}
      xKey="run"
      lines={[{ key: "risk", label: "Bias risk score" }]}
    />
  );
};
