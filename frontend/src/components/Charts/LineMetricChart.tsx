import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { AccessibleChartCard } from "@/components/Charts/AccessibleChartCard";
import { chartPalette } from "@/utils/chartPalette";

export const LineMetricChart = ({
  title,
  description,
  summary,
  data,
  xKey,
  lines,
}: {
  title: string;
  description: string;
  summary: string;
  data: Record<string, number | string>[];
  xKey: string;
  lines: Array<{ key: string; label: string; color?: string }>;
}) => (
  <AccessibleChartCard title={title} description={description} summary={summary}>
    <ResponsiveContainer>
      <LineChart data={data}>
        <CartesianGrid strokeDasharray="3 3" vertical={false} />
        <XAxis dataKey={xKey} />
        <YAxis />
        <Tooltip />
        <Legend />
        {lines.map((line, index) => (
          <Line
            key={line.key}
            type="monotone"
            dataKey={line.key}
            name={line.label}
            stroke={line.color ?? [chartPalette.indigo, chartPalette.amber, chartPalette.rose, chartPalette.teal][index % 4]}
            strokeWidth={2.5}
            dot={{ r: 3 }}
          />
        ))}
      </LineChart>
    </ResponsiveContainer>
  </AccessibleChartCard>
);

