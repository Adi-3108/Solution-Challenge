import { ApiResponse, AuditLogRecord, User } from "@/types/api";

import { httpClient } from "@/services/http";

export const adminService = {
  users: async (): Promise<User[]> => {
    const response = await httpClient.get<ApiResponse<User[]>>("/admin/users");
    return response.data.data;
  },
  auditLog: async (): Promise<AuditLogRecord[]> => {
    const response = await httpClient.get<ApiResponse<AuditLogRecord[]>>("/admin/audit-log");
    return response.data.data;
  },
  updateUserRole: async (userId: string, role: User["role"]): Promise<User> => {
    const response = await httpClient.patch<ApiResponse<User>>(`/admin/users/${userId}`, { role });
    return response.data.data;
  },
};

