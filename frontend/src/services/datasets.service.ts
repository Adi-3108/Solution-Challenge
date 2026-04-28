import { ApiResponse, DatasetRecord, ModelRecord } from "@/types/api";

import { httpClient } from "@/services/http";

export type DatasetUploadPayload = {
  projectId: string;
  datasetFile: File;
  targetColumn: string;
  protectedColumns: string[];
  positiveLabel: string;
  predictionColumn?: string;
  scoreColumn?: string;
};

export type ModelUploadPayload = {
  projectId: string;
  modelFile: File;
};

export const datasetsService = {
  uploadDataset: async (payload: DatasetUploadPayload): Promise<DatasetRecord> => {
    const formData = new FormData();
    formData.append("file", payload.datasetFile);
    formData.append("target_column", payload.targetColumn);
    formData.append("protected_columns", JSON.stringify(payload.protectedColumns));
    formData.append("positive_label", payload.positiveLabel);
    if (payload.predictionColumn) {
      formData.append("prediction_column", payload.predictionColumn);
    }
    if (payload.scoreColumn) {
      formData.append("score_column", payload.scoreColumn);
    }
    const response = await httpClient.post<ApiResponse<DatasetRecord>>(
      `/projects/${payload.projectId}/datasets`,
      formData,
      { headers: { "Content-Type": "multipart/form-data" } },
    );
    return response.data.data;
  },
  uploadModel: async (payload: ModelUploadPayload): Promise<ModelRecord> => {
    const formData = new FormData();
    formData.append("file", payload.modelFile);
    const response = await httpClient.post<ApiResponse<ModelRecord>>(
      `/projects/${payload.projectId}/models`,
      formData,
      { headers: { "Content-Type": "multipart/form-data" } },
    );
    return response.data.data;
  },
  preview: async (datasetId: string): Promise<ApiResponse<{ dataset_id: string; preview_rows: Record<string, unknown>[]; column_types: Record<string, string> }>> => {
    const response = await httpClient.get<ApiResponse<{ dataset_id: string; preview_rows: Record<string, unknown>[]; column_types: Record<string, string> }>>(`/datasets/${datasetId}/preview`);
    return response.data;
  },
};

