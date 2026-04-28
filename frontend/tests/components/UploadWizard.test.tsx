import { fireEvent, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { UploadWizard } from "@/components/Projects/UploadWizard";
import { renderWithProviders } from "../test-utils";

vi.mock("@/services/datasets.service", () => ({
  datasetsService: {
    uploadDataset: vi.fn(async () => ({ id: "dataset-1" })),
    uploadModel: vi.fn(async () => ({ id: "model-1" })),
  },
}));

vi.mock("@/services/runs.service", () => ({
  runsService: {
    create: vi.fn(async () => ({ id: "run-1" })),
  },
}));

describe("UploadWizard", () => {
  it("shows validation and supports next/back navigation", async () => {
    renderWithProviders(<UploadWizard projectId="project-1" onCompleted={vi.fn()} />);

    fireEvent.click(screen.getByRole("button", { name: "Continue" }));
    expect(await screen.findByText("Choose a dataset file.")).toBeInTheDocument();

    const fileInput = screen.getByLabelText(/drag a file here or click to browse/i) as HTMLInputElement;
    const file = new File(["gender,target\nF,1"], "audit.csv", { type: "text/csv" });
    fireEvent.change(fileInput, { target: { files: [file] } });

    fireEvent.click(screen.getByRole("button", { name: "Continue" }));
    await screen.findByText("Configure audit");

    fireEvent.click(screen.getByRole("button", { name: "Back" }));
    await screen.findByText("Upload dataset");
  });
});
