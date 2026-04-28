import { ApiResponse, ProjectDetail, ProjectSummary } from "@/types/api";
import { ProjectValues } from "@/schemas/project.schema";

import { httpClient } from "@/services/http";

type ProjectListQuery = {
  cursor?: string | null;
};

export const projectsService = {
  list: async (query: ProjectListQuery = {}): Promise<ApiResponse<ProjectSummary[]>> => {
    const response = await httpClient.get<ApiResponse<ProjectSummary[]>>("/projects", {
      params: { cursor: query.cursor ?? undefined },
    });
    return response.data;
  },
  create: async (payload: ProjectValues): Promise<ProjectSummary> => {
    const response = await httpClient.post<ApiResponse<ProjectSummary>>("/projects", payload);
    return response.data.data;
  },
  detail: async (projectId: string): Promise<ProjectDetail> => {
    const response = await httpClient.get<ApiResponse<ProjectDetail>>(`/projects/${projectId}`);
    return response.data.data;
  },
  update: async (projectId: string, payload: Partial<ProjectValues>): Promise<ProjectSummary> => {
    const response = await httpClient.patch<ApiResponse<ProjectSummary>>(`/projects/${projectId}`, payload);
    return response.data.data;
  },
  archive: async (projectId: string): Promise<void> => {
    await httpClient.delete(`/projects/${projectId}`);
  },
};

