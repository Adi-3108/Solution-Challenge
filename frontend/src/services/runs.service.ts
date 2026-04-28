import { ApiResponse, ReportRecord, RunResultsPayload, RunSummary } from "@/types/api";

import { resolveApiBaseUrl } from "@/services/apiBaseUrl";
import { httpClient } from "@/services/http";

type RunListResponse = ApiResponse<RunSummary[]>;
const reportApiBaseUrl = resolveApiBaseUrl();

const inferReportFilename = (
  contentDisposition: string | undefined,
  runId: string,
  format: "pdf" | "json",
): string => {
  const match = contentDisposition?.match(/filename="?([^"]+)"?/i);
  return match?.[1] ?? `${runId}.${format}`;
};

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
  reportDownloadUrl: (runId: string, format: "pdf" | "json"): string =>
    `${reportApiBaseUrl}/runs/${runId}/report/${format}`,
  downloadReport: async (runId: string, format: "pdf" | "json"): Promise<void> => {
    const response = await httpClient.get<Blob>(`/runs/${runId}/report/${format}`, {
      responseType: "blob",
    });
    const blobUrl = window.URL.createObjectURL(response.data);
    const downloadLink = document.createElement("a");
    downloadLink.href = blobUrl;
    downloadLink.download = inferReportFilename(response.headers["content-disposition"], runId, format);
    document.body.appendChild(downloadLink);
    downloadLink.click();
    downloadLink.remove();
    window.URL.revokeObjectURL(blobUrl);
  },
};
