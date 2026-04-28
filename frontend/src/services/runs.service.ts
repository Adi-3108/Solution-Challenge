import { ApiResponse, ReportRecord, RunResultsPayload, RunSummary } from "@/types/api";

import { httpClient } from "@/services/http";

type RunListResponse = ApiResponse<RunSummary[]>;

export const runsService = {
  create: async (projectId: string, payload: { dataset_id: string; model_id?: string | null; thresholds?: Record<string, unknown> }): Promise<RunSummary> => {
    const response = await httpClient.post<ApiResponse<RunSummary>>(`/projects/${projectId}/runs`, payload);
    return response.data.data;
  },
  list: async (projectId: string, cursor?: string | null): Promise<RunListResponse> => {
    const response = await httpClient.get<RunListResponse>(`/projects/${projectId}/runs`, {
      params: { cursor: cursor ?? undefined },
    });
    return response.data;
  },
  detail: async (runId: string): Promise<RunSummary> => {
    const response = await httpClient.get<ApiResponse<RunSummary>>(`/runs/${runId}`);
    return response.data.data;
  },
  results: async (runId: string): Promise<RunResultsPayload> => {
    const response = await httpClient.get<ApiResponse<RunResultsPayload>>(`/runs/${runId}/results`);
    return response.data.data;
  },
  shap: async (runId: string): Promise<ApiResponse<RunResultsPayload["shap"]>> => {
    const response = await httpClient.get<ApiResponse<RunResultsPayload["shap"]>>(`/runs/${runId}/shap`);
    return response.data;
  },
  generateReport: async (runId: string, format: "pdf" | "json"): Promise<ReportRecord> => {
    const response = await httpClient.post<ApiResponse<ReportRecord>>(`/runs/${runId}/report`, { format });
    return response.data.data;
  },
  reportDownloadUrl: (runId: string, format: "pdf" | "json"): string => `/api/v1/runs/${runId}/report/${format}`,
};

