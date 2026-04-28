import { describe, expect, it } from "vitest";

import { loginSchema, registerSchema } from "@/schemas/auth.schema";

describe("auth schemas", () => {
  it("rejects invalid login payloads", () => {
    const result = loginSchema.safeParse({ email: "bad-email", password: "123" });
    expect(result.success).toBe(false);
  });

  it("accepts valid registration payloads", () => {
    const result = registerSchema.safeParse({
      email: "analyst@fairsight.demo",
      password: "Demo1234!",
      role: "analyst",
    });
    expect(result.success).toBe(true);
  });
});

