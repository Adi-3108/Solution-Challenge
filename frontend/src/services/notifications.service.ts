import { ApiResponse, NotificationRecord } from "@/types/api";

import { httpClient } from "@/services/http";

export const notificationsService = {
  list: async (projectId: string): Promise<NotificationRecord[]> => {
    const response = await httpClient.get<ApiResponse<NotificationRecord[]>>(
      `/projects/${projectId}/notifications`,
    );
    return response.data.data;
  },
  update: async (projectId: string, notifications: NotificationRecord[]): Promise<void> => {
    await httpClient.put(`/projects/${projectId}/notifications`, {
      notifications: notifications.map(({ type, destination, enabled }) => ({
        type,
        destination,
        enabled,
      })),
    });
  },
};

