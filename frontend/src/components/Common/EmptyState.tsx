import { ReactNode } from "react";

type EmptyStateProps = {
  title: string;
  description: string;
  action?: ReactNode;
};

export const EmptyState = ({ title, description, action }: EmptyStateProps) => (
  <div className="panel-muted flex flex-col items-center justify-center gap-4 px-6 py-12 text-center">
    <div className="rounded-full bg-brand-600/10 p-4 text-brand-700 dark:text-brand-200">
      <div className="h-8 w-8 rounded-full border-2 border-current" />
    </div>
    <div className="space-y-1">
      <h3 className="text-lg font-semibold text-slate-900 dark:text-slate-50">{title}</h3>
      <p className="max-w-lg text-sm text-slate-600 dark:text-slate-300">{description}</p>
    </div>
    {action}
  </div>
);

