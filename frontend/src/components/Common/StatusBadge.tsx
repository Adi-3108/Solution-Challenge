import { AlertTriangle, CheckCircle, XCircle } from "lucide-react";

import { Severity } from "@/types/api";
import { cn } from "@/utils/cn";
import { severityLabel } from "@/utils/format";

const config = {
  green: {
    className:
      "border border-emerald-200 bg-emerald-50 text-emerald-700 dark:border-emerald-900/60 dark:bg-emerald-950/60 dark:text-emerald-200",
    Icon: CheckCircle,
  },
  amber: {
    className:
      "border border-amber-200 bg-amber-50 text-amber-700 dark:border-amber-900/60 dark:bg-amber-950/60 dark:text-amber-200",
    Icon: AlertTriangle,
  },
  red: {
    className:
      "border border-rose-200 bg-rose-50 text-rose-700 dark:border-rose-900/60 dark:bg-rose-950/60 dark:text-rose-200",
    Icon: XCircle,
  },
} as const;

export const StatusBadge = ({ severity }: { severity: Severity }) => {
  const { Icon, className } = config[severity];
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium",
        className,
      )}
    >
      <Icon className="h-3.5 w-3.5" />
      {severityLabel(severity)}
    </span>
  );
};

