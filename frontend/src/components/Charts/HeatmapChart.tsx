import {
  CartesianGrid,
  ResponsiveContainer,
  Scatter,
  ScatterChart,
  Tooltip,
  XAxis,
  YAxis,
  ZAxis,
} from "recharts";

import { AccessibleChartCard } from "@/components/Charts/AccessibleChartCard";

export type HeatmapDatum = {
  x: number;
  y: number;
  z: number;
  xLabel: string;
  yLabel: string;
};

type HeatmapShapeProps = {
  cx?: number;
  cy?: number;
  payload: HeatmapDatum;
};

const isHeatmapShapeProps = (value: unknown): value is HeatmapShapeProps => {
  if (typeof value !== "object" || value === null) {
    return false;
  }
  const candidate = value as Record<string, unknown>;
  return typeof candidate.payload === "object" && candidate.payload !== null;
};

const colorForValue = (value: number): string => {
  if (value >= 0.8) {
    return "#DC2626";
  }
  if (value >= 0.5) {
    return "#D97706";
  }
  return "#4F46E5";
};

export const HeatmapChart = ({
  title,
  description,
  summary,
  data,
}: {
  title: string;
  description: string;
  summary: string;
  data: HeatmapDatum[];
}) => (
  <AccessibleChartCard title={title} description={description} summary={summary}>
    <ResponsiveContainer>
      <ScatterChart margin={{ top: 20, right: 30, left: 20, bottom: 20 }}>
        <CartesianGrid />
        <XAxis
          dataKey="x"
          type="number"
          tickFormatter={(value) => data.find((item) => item.x === value)?.xLabel ?? String(value)}
          allowDecimals={false}
        />
        <YAxis
          dataKey="y"
          type="number"
          tickFormatter={(value) => data.find((item) => item.y === value)?.yLabel ?? String(value)}
          allowDecimals={false}
        />
        <ZAxis dataKey="z" range={[280, 280]} />
        <Tooltip
          formatter={(value: number) => value.toFixed(3)}
          labelFormatter={(_, payload) =>
            payload[0]
              ? `${payload[0].payload.yLabel} x ${payload[0].payload.xLabel}`
              : ""
          }
        />
        <Scatter
          data={data}
          shape={(props: unknown) => {
            if (!isHeatmapShapeProps(props)) {
              return <></>;
            }
            const fill = colorForValue(Number(props.payload.z));
            return (
              <rect
                x={(props.cx ?? 0) - 18}
                y={(props.cy ?? 0) - 18}
                width={36}
                height={36}
                rx={8}
                fill={fill}
                fillOpacity={0.85}
              />
            );
          }}
        />
      </ScatterChart>
    </ResponsiveContainer>
  </AccessibleChartCard>
);
