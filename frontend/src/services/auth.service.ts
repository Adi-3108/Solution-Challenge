import { ApiResponse, AuthResponse, User } from "@/types/api";

import { httpClient } from "@/services/http";
import { LoginValues, RegisterValues } from "@/schemas/auth.schema";

export const authService = {
  login: async (payload: LoginValues): Promise<AuthResponse> => {
    const response = await httpClient.post<ApiResponse<AuthResponse>>("/auth/login", payload);
    return response.data.data;
  },
  register: async (payload: RegisterValues): Promise<AuthResponse> => {
    const response = await httpClient.post<ApiResponse<AuthResponse>>("/auth/register", payload);
    return response.data.data;
  },
  logout: async (): Promise<void> => {
    await httpClient.post("/auth/logout");
  },
  googleLogin: async (credential: string): Promise<AuthResponse> => {
    const response = await httpClient.post<ApiResponse<AuthResponse>>("/auth/google", { credential });
    return response.data.data;
  },
  me: async (): Promise<User> => {
    const response = await httpClient.get<ApiResponse<User>>("/auth/me");
    return response.data.data;
  },
  requestReset: async (email: string): Promise<void> => {
    await httpClient.post("/auth/reset-password/request", { email });
  },
  confirmReset: async (token: string, newPassword: string): Promise<void> => {
    await httpClient.post("/auth/reset-password/confirm", {
      token,
      new_password: newPassword,
    });
  },
};

