import { act, renderHook } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { useToast } from "@/hooks/useToast";

describe("useToast", () => {
  it("adds and removes toasts", () => {
    const { result } = renderHook(() => useToast());

    act(() => {
      result.current.showInfo("Saved", "The project was created.");
    });

    expect(result.current.toasts).toHaveLength(1);

    act(() => {
      result.current.removeToast(result.current.toasts[0].id);
    });

    expect(result.current.toasts).toHaveLength(0);
  });
});

