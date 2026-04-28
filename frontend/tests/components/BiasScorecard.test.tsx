import { screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { BiasScorecard } from "@/components/Runs/BiasScorecard";
import { renderWithProviders } from "../test-utils";

describe("BiasScorecard", () => {
  it("renders metric cards with readable rag status", () => {
    renderWithProviders(
      <BiasScorecard
        metrics={[
          {
            metric_name: "statistical_parity_difference",
            display_name: "Statistical Parity Difference",
            group_name: "gender",
            value: 0.24,
            severity: "red",
            threshold_used: 0.1,
            explanation: "Bias detected for women.",
          },
        ]}
      />,
    );

    expect(screen.getByText("Statistical Parity Difference")).toBeInTheDocument();
    expect(screen.getByText("Bias detected")).toBeInTheDocument();
  });
});
