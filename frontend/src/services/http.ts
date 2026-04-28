import axios, { AxiosError, InternalAxiosRequestConfig } from "axios";

import { resolveApiBaseUrl } from "@/services/apiBaseUrl";
import { useAuthStore } from "@/stores/auth.store";
import { ApiError } from "@/types/api";
import { logger } from "@/utils/logger";

const apiBaseUrl = resolveApiBaseUrl();

export const httpClient = axios.create({
  baseURL: apiBaseUrl,
  withCredentials: true,
  headers: {
    "Content-Type": "application/json",
  },
});

const refreshClient = axios.create({
  baseURL: apiBaseUrl,
  withCredentials: true,
  headers: {
    "Content-Type": "application/json",
  },
});

type RetryableRequestConfig = InternalAxiosRequestConfig & { _retry?: boolean };

let refreshPromise: Promise<void> | null = null;

const refreshAccessToken = async (): Promise<void> => {
  if (!refreshPromise) {
    refreshPromise = refreshClient.post("/auth/refresh").then(() => undefined).finally(() => {
      refreshPromise = null;
    });
  }
  return refreshPromise;
};

httpClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError<ApiError>) => {
    const status = error.response?.status;
    const config = error.config as RetryableRequestConfig | undefined;
    const url = config?.url ?? "";
    const isAuthEndpoint =
      url.includes("/auth/login") || url.includes("/auth/register") || url.includes("/auth/refresh");

    if (status === 401 && config && !config._retry && !isAuthEndpoint) {
      config._retry = true;
      try {
        await refreshAccessToken();
        return httpClient(config);
      } catch {
        useAuthStore.getState().reset();
        window.location.assign("/login");
        return Promise.reject(error);
      }
    }

    if (status === 401) {
      useAuthStore.getState().reset();
      window.location.assign("/login");
    }
    logger.error("api_request_failed", {
      url,
      status,
      code: error.response?.data?.error.code,
    });
    return Promise.reject(error);
  },
);

export const getErrorMessage = (error: unknown): string => {
  if (axios.isAxiosError<ApiError>(error)) {
    return error.response?.data?.error.message ?? "Connection problem - please try again";
  }
  return "Connection problem - please try again";
};
