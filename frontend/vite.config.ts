import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "node:path";

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  server: {
    host: "0.0.0.0",
    port: 5173,
  },
  preview: {
    host: "0.0.0.0",
    port: 4173,
  },
  test: {
    environment: "jsdom",
    setupFiles: "./vitest.setup.ts",
    exclude: ["tests/e2e/**", "node_modules/**"],
    coverage: {
      reporter: ["text", "html"],
      include: ["src/utils/**", "src/services/**", "src/hooks/**", "src/schemas/**"],
    },
  },
});
