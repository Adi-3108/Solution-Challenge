import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { Plus } from "lucide-react";

import { Button } from "@/components/Common/Button";
import { EmptyState } from "@/components/Common/EmptyState";
import { PageHeader } from "@/components/Common/PageHeader";
import { ProjectCard } from "@/components/Dashboard/ProjectCard";
import { projectSchema, ProjectValues } from "@/schemas/project.schema";
import { projectsService } from "@/services/projects.service";

export const DashboardPage = () => {
  const queryClient = useQueryClient();
  const projectsQuery = useQuery({
    queryKey: ["projects"],
    queryFn: () => projectsService.list(),
  });
  const form = useForm<ProjectValues>({
    resolver: zodResolver(projectSchema),
  });
  const createMutation = useMutation({
    mutationFn: projectsService.create,
    onSuccess: () => {
      form.reset();
      queryClient.invalidateQueries({ queryKey: ["projects"] });
    },
  });

  const projects = projectsQuery.data?.data ?? [];

  return (
    <div className="space-y-8">
      <PageHeader
        title="Projects dashboard"
        subtitle="Review recent audits, compare risk levels, and create a new project when a dataset or model needs fairness review."
        action={
          <Button
            type="button"
            onClick={() => document.getElementById("new-project-form")?.scrollIntoView({ behavior: "smooth" })}
          >
            <Plus className="mr-2 h-4 w-4" />
            New project
          </Button>
        }
      />

      <section className="grid gap-6 xl:grid-cols-[1.3fr_0.7fr]">
        <div className="space-y-4">
          {projects.length > 0 ? (
            <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
              {projects.map((project) => (
                <ProjectCard key={project.id} project={project} />
              ))}
            </div>
          ) : (
            <EmptyState
              title="No audit projects yet"
              description="Create a named project to organize datasets, models, and historical audit runs."
            />
          )}
        </div>
        <form
          id="new-project-form"
          onSubmit={form.handleSubmit((values) => createMutation.mutate(values))}
          className="panel space-y-4 p-5"
        >
          <div>
            <h2 className="text-lg font-semibold text-slate-950 dark:text-white">Create a project</h2>
            <p className="text-sm text-slate-600 dark:text-slate-300">
              Example: Q3 Hiring Model Audit or Lending Score Retrospective.
            </p>
          </div>
          <label className="space-y-2">
            <span className="font-medium text-slate-700 dark:text-slate-100">Project name</span>
            <input className="button-secondary w-full justify-start text-left font-normal" {...form.register("name")} />
            {form.formState.errors.name && (
              <p className="text-sm text-rose-600">{form.formState.errors.name.message}</p>
            )}
          </label>
          <label className="space-y-2">
            <span className="font-medium text-slate-700 dark:text-slate-100">Description</span>
            <textarea
              rows={5}
              className="w-full rounded-lg border border-slate-300 bg-white px-4 py-3 text-sm text-slate-700 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100"
              {...form.register("description")}
            />
          </label>
          <Button type="submit" className="w-full" disabled={createMutation.isPending}>
            {createMutation.isPending ? "Creating project..." : "Create project"}
          </Button>
        </form>
      </section>
    </div>
  );
};
