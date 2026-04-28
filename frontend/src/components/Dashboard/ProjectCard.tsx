import { Link } from "react-router-dom";

import { Card } from "@/components/Common/Card";
import { StatusBadge } from "@/components/Common/StatusBadge";
import { ProjectSummary } from "@/types/api";
import { formatDate } from "@/utils/format";

export const ProjectCard = ({ project }: { project: ProjectSummary }) => {
  const severity =
    project.last_run_status === "failed"
      ? "red"
      : project.last_run_status === "queued" || project.last_run_status === "running"
        ? "amber"
        : project.risk_score === null
          ? "green"
          : project.risk_score >= 70
            ? "red"
            : project.risk_score >= 40
              ? "amber"
              : "green";
  return (
    <Link to={`/projects/${project.id}`} className="block">
      <Card className="h-full space-y-4 transition hover:-translate-y-1 hover:shadow-panel">
        <div className="flex items-start justify-between gap-3">
          <div className="space-y-2">
            <h3 className="text-lg font-semibold text-slate-950 dark:text-white">{project.name}</h3>
            <p className="text-sm text-slate-600 dark:text-slate-300">
              {project.description ?? "No description yet."}
            </p>
          </div>
          <StatusBadge severity={severity} />
        </div>
        <div className="grid grid-cols-2 gap-3 text-sm">
          <div className="rounded-xl bg-slate-50 p-3 dark:bg-slate-900/60">
            <p className="text-slate-500 dark:text-slate-400">Last run</p>
            <p className="mt-1 font-medium text-slate-950 dark:text-white">
              {formatDate(project.last_run_date)}
            </p>
            <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
              {project.last_run_status ?? "No runs yet"}
            </p>
          </div>
          <div className="rounded-xl bg-slate-50 p-3 dark:bg-slate-900/60">
            <p className="text-slate-500 dark:text-slate-400">Audit runs</p>
            <p className="mt-1 font-medium text-slate-950 dark:text-white">{project.run_count}</p>
          </div>
        </div>
      </Card>
    </Link>
  );
};
