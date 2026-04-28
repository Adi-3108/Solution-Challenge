import { Severity } from "@/types/api";

export const formatDate = (value: string | null): string => {
  if (!value) {
    return "Not available";
  }
  return new Intl.DateTimeFormat("en-US", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
};

export const formatPercent = (value: number, digits = 1): string => `${(value * 100).toFixed(digits)}%`;

export const formatSignedNumber = (value: number, digits = 2): string => {
  const prefix = value > 0 ? "+" : "";
  return `${prefix}${value.toFixed(digits)}`;
};

export const formatMetricValue = (metricName: string, value: number): string => {
  if (metricName.includes("ratio") || metricName.includes("score")) {
    return value.toFixed(2);
  }
  return value.toFixed(3);
};

export const severityLabel = (severity: Severity): string => {
  if (severity === "green") {
    return "Meets fairness standard";
  }
  if (severity === "amber") {
    return "Approaching concern";
  }
  return "Bias detected";
};
