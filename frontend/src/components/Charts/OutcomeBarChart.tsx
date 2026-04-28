import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { AccessibleChartCard } from "@/components/Charts/AccessibleChartCard";
import { chartPalette } from "@/utils/chartPalette";

type OutcomeBarChartProps = {
  title: string;
  description: string;
  data: Array<{ group: string; positive_rate: number; count?: number }>;
  summary: string;
};

export const OutcomeBarChart = ({
  title,
  description,
  data,
  summary,
}: OutcomeBarChartProps) => (
  <AccessibleChartCard title={title} description={description} summary={summary}>
    <ResponsiveContainer>
      <BarChart data={data}>
        <CartesianGrid strokeDasharray="3 3" vertical={false} />
        <XAxis dataKey="group" />
        <YAxis domain={[0, 1]} />
        <Tooltip formatter={(value: number) => `${(value * 100).toFixed(1)}%`} />
        <Legend />
        <Bar name="Positive outcome rate" dataKey="positive_rate" fill={chartPalette.indigo} radius={[8, 8, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  </AccessibleChartCard>
);

