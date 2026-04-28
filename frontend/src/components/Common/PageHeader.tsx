import { ReactNode } from "react";

type PageHeaderProps = {
  title: string;
  subtitle: string;
  action?: ReactNode;
};

export const PageHeader = ({ title, subtitle, action }: PageHeaderProps) => (
  <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
    <div className="space-y-2">
      <p className="text-xs font-semibold uppercase tracking-[0.24em] text-brand-700 dark:text-brand-300">
        FairSight
      </p>
      <h1 className="text-2xl font-semibold text-slate-950 dark:text-white">{title}</h1>
      <p className="max-w-3xl text-sm text-slate-600 dark:text-slate-300">{subtitle}</p>
    </div>
    {action}
  </div>
);

