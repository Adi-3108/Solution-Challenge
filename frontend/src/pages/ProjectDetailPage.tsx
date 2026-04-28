import { Link, useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { Plus } from "lucide-react";

import { Button } from "@/components/Common/Button";
import { Card } from "@/components/Common/Card";
import { EmptyState } from "@/components/Common/EmptyState";
import { PageHeader } from "@/components/Common/PageHeader";
import { StatusBadge } from "@/components/Common/StatusBadge";
import { projectsService } from "@/services/projects.service";
import { formatDate } from "@/utils/format";

export const ProjectDetailPage = () => {
  const { projectId = "" } = useParams();
  const projectQuery = useQuery({
    queryKey: ["project", projectId],
    queryFn: () => projectsService.detail(projectId),
  });

  const project = projectQuery.data;
  if (!project) {
    return <div className="panel p-6">Loading project...</div>;
  }

  const runSeverity = (run: (typeof project.runs)[number]) => {
    if (run.status === "failed") {
      return "red" as const;
    }
    if (run.status === "queued" || run.status === "running") {
      return "amber" as const;
    }
    if (run.bias_risk_score === null) {
      return "green" as const;
    }
    if (run.bias_risk_score >= 70) {
      return "red" as const;
    }
    if (run.bias_risk_score >= 40) {
      return "amber" as const;
    }
    return "green" as const;
  };

  return (
    <div className="space-y-8">
      <PageHeader
        title={project.name}
        subtitle={project.description ?? "Track datasets, model artifacts, and audit history for this project."}
        action={
          <Link to={`/projects/${project.id}/upload`}>
            <Button type="button">
              <Plus className="mr-2 h-4 w-4" />
              Run new audit
            </Button>
          </Link>
        }
      />

      <section className="grid gap-6 lg:grid-cols-3">
        <Card className="space-y-3">
          <h2 className="text-lg font-semibold text-slate-950 dark:text-white">Datasets</h2>
          {project.datasets.length > 0 ? (
            <ul className="space-y-3">
              {project.datasets.map((dataset) => (
                <li key={dataset.id} className="rounded-xl bg-slate-50 p-3 dark:bg-slate-900/60">
                  <p className="font-medium text-slate-950 dark:text-white">{dataset.filename}</p>
                  <p className="text-xs text-slate-500 dark:text-slate-400">
                    {dataset.row_count} rows | target {dataset.target_column}
                  </p>
                </li>
              ))}
            </ul>
          ) : (
            <EmptyState title="No datasets yet" description="Upload your first dataset through the audit wizard." />
          )}
        </Card>
        <Card className="space-y-3">
          <h2 className="text-lg font-semibold text-slate-950 dark:text-white">Models</h2>
          {project.models.length > 0 ? (
            <ul className="space-y-3">
              {project.models.map((model) => (
                <li key={model.id} className="rounded-xl bg-slate-50 p-3 dark:bg-slate-900/60">
                  <p className="font-medium text-slate-950 dark:text-white">{model.filename}</p>
                  <p className="text-xs text-slate-500 dark:text-slate-400">{model.model_type}</p>
                </li>
              ))}
            </ul>
          ) : (
            <EmptyState title="No model artifacts yet" description="Upload a model in the audit wizard to unlock explainability." />
          )}
        </Card>
        <Card className="space-y-3">
          <h2 className="text-lg font-semibold text-slate-950 dark:text-white">Recent runs</h2>
          {project.runs.length > 0 ? (
            <ul className="space-y-3">
              {project.runs.map((run) => (
                <li key={run.id} className="rounded-xl bg-slate-50 p-3 dark:bg-slate-900/60">
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <Link to={`/runs/${run.id}`} className="font-medium text-brand-700 dark:text-brand-300">
                        View audit run
                      </Link>
                      <p className="text-xs text-slate-500 dark:text-slate-400">
                        {run.status} | {formatDate(run.completed_at ?? run.started_at)}
                      </p>
                    </div>
                    <StatusBadge severity={runSeverity(run)} />
                  </div>
                </li>
              ))}
            </ul>
          ) : (
            <EmptyState title="No audits yet" description="Run an audit to generate fairness metrics and reports." />
          )}
        </Card>
      </section>
    </div>
  );
};
