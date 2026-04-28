import { RunSummary } from "@/types/api";

const stages = [
  "Analyzing distributions...",
  "Computing fairness metrics...",
  "Running intersectional analysis...",
  "Generating explanations...",
  "Completed",
];

export const AuditProgress = ({ run }: { run: RunSummary }) => {
  const activeIndex = Math.max(0, stages.findIndex((stage) => run.stage_label.includes(stage.slice(0, 10))));
  return (
    <div className="panel space-y-4 p-5">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-slate-950 dark:text-white">Audit progress</h3>
        <span className="font-medium text-slate-600 dark:text-slate-300">{run.status}</span>
      </div>
      <div className="grid gap-3 md:grid-cols-5">
        {stages.map((stage, index) => (
          <div key={stage} className="space-y-2">
            <div className={`h-2 rounded-full ${index <= activeIndex ? "bg-brand-600" : "bg-slate-200 dark:bg-slate-700"}`} />
            <p className="text-xs text-slate-500 dark:text-slate-400">{stage}</p>
          </div>
        ))}
      </div>
    </div>
  );
};

