import { renderHook, act } from "@testing-library/react";
import { describe, expect, it, vi, afterEach } from "vitest";

import { usePredict } from "@/components/predict/use-predict";

afterEach(() => {
  vi.restoreAllMocks();
});

function mockFetchSuccess() {
  const payload = {
    ok: true,
    fixture: {
      season: "2023-2024",
      home: { name: "Arsenal", shortName: "ARS" },
      away: { name: "Chelsea", shortName: "CHE" },
    },
    models: [
      {
        id: "mock",
        format: "tfjs",
        location: null,
        probs: { home: 0.5, draw: 0.2, away: 0.3 },
        logits: { home: 0.5, draw: -0.2, away: -0.3 },
        note: "mock",
      },
    ],
    ensemble: {
      method: "avg",
      probs: { home: 0.5, draw: 0.2, away: 0.3 },
    },
  };
  vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(
    new Response(JSON.stringify(payload), { status: 200 }),
  );
}

describe("usePredict hook", () => {
  it("sets success state on payload", async () => {
    mockFetchSuccess();
    const { result } = renderHook(() => usePredict());

    await act(async () => {
      await result.current.predict("Arsenal", "Chelsea");
    });

    expect(result.current.status).toBe("success");
    expect(result.current.data?.ensemble.probs.home).toBeCloseTo(0.5);
  });

  it("handles errors", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(
      new Response(JSON.stringify({ ok: false, error: "bad" }), { status: 400 }),
    );
    const { result } = renderHook(() => usePredict());

    await act(async () => {
      await result.current.predict("Arsenal", "Unknown");
    });

    expect(result.current.status).toBe("error");
    expect(result.current.error).toBeDefined();
  });
});
