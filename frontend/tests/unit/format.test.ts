import { describe, expect, it } from "vitest";

import { formatMetricValue, severityLabel } from "@/utils/format";

describe("format helpers", () => {
  it("formats ratio values with two decimals", () => {
    expect(formatMetricValue("disparate_impact_ratio", 0.81234)).toBe("0.81");
  });

  it("returns accessible severity labels", () => {
    expect(severityLabel("red")).toBe("Bias detected");
  });
});

