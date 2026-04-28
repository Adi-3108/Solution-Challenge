import { PolarAngleAxis, RadialBar, RadialBarChart, ResponsiveContainer } from "recharts";

import { AccessibleChartCard } from "@/components/Charts/AccessibleChartCard";
import { severityColor } from "@/utils/chartPalette";

export const RiskGauge = ({ score }: { score: number | null }) => {
  const normalizedScore = Math.max(0, Math.min(score ?? 0, 100));
  const tone = normalizedScore >= 70 ? "red" : normalizedScore >= 40 ? "amber" : "green";
  return (
    <AccessibleChartCard
      title="Bias risk score"
      description="A weighted summary of fairness warnings and failures across this audit run."
      summary={`Bias risk score is ${normalizedScore} out of 100.`}
    >
      <ResponsiveContainer>
        <RadialBarChart
          data={[{ name: "Risk", value: normalizedScore, fill: severityColor[tone] }]}
          innerRadius="68%"
          outerRadius="100%"
          startAngle={210}
          endAngle={-30}
          barSize={18}
        >
          <PolarAngleAxis domain={[0, 100]} tick={false} type="number" />
          <RadialBar dataKey="value" cornerRadius={12} background />
          <text x="50%" y="48%" textAnchor="middle" className="fill-slate-900 font-mono text-4xl dark:fill-white">
            {normalizedScore.toFixed(0)}
          </text>
          <text x="50%" y="58%" textAnchor="middle" className="fill-slate-500 text-sm dark:fill-slate-300">
            out of 100
          </text>
        </RadialBarChart>
      </ResponsiveContainer>
    </AccessibleChartCard>
  );
};

