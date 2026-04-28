import { ReactNode } from "react";

import { Card } from "@/components/Common/Card";

type AccessibleChartCardProps = {
  title: string;
  description: string;
  summary: string;
  children: ReactNode;
};

export const AccessibleChartCard = ({
  title,
  description,
  summary,
  children,
}: AccessibleChartCardProps) => (
  <Card className="space-y-4" aria-label={title}>
    <div className="space-y-1">
      <h3 className="text-lg font-semibold text-slate-950 dark:text-white">{title}</h3>
      <p className="text-sm text-slate-600 dark:text-slate-300">{description}</p>
      <p className="sr-only">{summary}</p>
    </div>
    <div className="h-80">{children}</div>
  </Card>
);

