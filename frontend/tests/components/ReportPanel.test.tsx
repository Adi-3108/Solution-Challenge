import { fireEvent, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { ReportPanel } from "@/components/Runs/ReportPanel";
import { renderWithProviders } from "../test-utils";

const { generateReport, downloadReport } = vi.hoisted(() => ({
  generateReport: vi.fn(async () => ({
    id: "report-1",
    run_id: "run-1",
    format: "pdf",
    file_hash: "hash",
    generated_at: "2026-04-28T00:00:00Z",
  })),
  downloadReport: vi.fn(async () => undefined),
}));

vi.mock("@/services/runs.service", () => ({
  runsService: {
    generateReport,
    downloadReport,
  },
}));

describe("ReportPanel", () => {
  it("triggers the report generation API", async () => {
    renderWithProviders(<ReportPanel runId="run-1" />);

    fireEvent.click(screen.getByRole("button", { name: /generate pdf report/i }));

    await waitFor(() => expect(generateReport).toHaveBeenCalledWith("run-1", "pdf"));
    await waitFor(() => expect(downloadReport).toHaveBeenCalledWith("run-1", "pdf"));
  });
});
