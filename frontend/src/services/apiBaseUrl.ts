const DEFAULT_API_BASE_PATH = "/api/v1";
const STANDALONE_FRONTEND_PORTS = new Set(["4173", "5173"]);

type LocationLike = Pick<Location, "hostname" | "port">;

export const resolveApiBaseUrl = (
  explicitBaseUrl = import.meta.env.VITE_API_BASE_URL,
  location: LocationLike | undefined = typeof window !== "undefined" ? window.location : undefined,
): string => {
  const trimmedBaseUrl = explicitBaseUrl?.trim();
  const withoutTrailingSlash = (value: string): string => value.replace(/\/+$/, "");
  if (trimmedBaseUrl) {
    // Avoid route-relative URLs like "api/v1" that break on nested frontend routes.
    if (/^https?:\/\//i.test(trimmedBaseUrl) || trimmedBaseUrl.startsWith("/")) {
      return withoutTrailingSlash(trimmedBaseUrl);
    }
    return withoutTrailingSlash(`/${trimmedBaseUrl}`);
  }

  if (location && STANDALONE_FRONTEND_PORTS.has(location.port)) {
    return `http://${location.hostname}:8000${DEFAULT_API_BASE_PATH}`;
  }

  return DEFAULT_API_BASE_PATH;
};
