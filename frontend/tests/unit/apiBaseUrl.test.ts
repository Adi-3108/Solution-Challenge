import { describe, expect, it } from "vitest";

import { resolveApiBaseUrl } from "@/services/apiBaseUrl";

describe("resolveApiBaseUrl", () => {
  it("prefers an explicit API base URL", () => {
    expect(resolveApiBaseUrl("https://api.example.com/v1", { hostname: "localhost", port: "4173" })).toBe(
      "https://api.example.com/v1",
    );
  });

  it("normalizes explicit path-only API base URLs", () => {
    expect(resolveApiBaseUrl("api/v1", { hostname: "localhost", port: "4173" })).toBe("/api/v1");
    expect(resolveApiBaseUrl("/api/v1", { hostname: "localhost", port: "4173" })).toBe("/api/v1");
  });

  it("targets the backend port when the UI is served from Vite dev or preview", () => {
    expect(resolveApiBaseUrl(undefined, { hostname: "localhost", port: "4173" })).toBe(
      "http://localhost:8000/api/v1",
    );
    expect(resolveApiBaseUrl(undefined, { hostname: "127.0.0.1", port: "5173" })).toBe(
      "http://127.0.0.1:8000/api/v1",
    );
  });

  it("keeps the relative API path when the app is behind nginx", () => {
    expect(resolveApiBaseUrl(undefined, { hostname: "localhost", port: "" })).toBe("/api/v1");
  });
});
