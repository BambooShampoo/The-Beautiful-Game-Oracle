import { http, HttpResponse } from "msw";
import { setupServer } from "msw/node";

const mockPrediction = {
  ok: true,
  fixture: {
    season: "2023-2024",
    home: { name: "Arsenal", shortName: "ARS" },
    away: { name: "Chelsea", shortName: "CHE" },
  },
  models: [
    {
      id: "performance_dense",
      format: "tfjs",
      location: { kind: "local", path: "/tmp/model.json" },
      probs: { home: 0.58, draw: 0.24, away: 0.18 },
      logits: { home: 0.5, draw: -0.3, away: -0.7 },
      note: "mock",
    },
  ],
  ensemble: {
    method: "avg",
    probs: { home: 0.58, draw: 0.24, away: 0.18 },
  },
};

const handlers = [
  http.get("/api/status", () =>
    HttpResponse.json({
      ok: true,
      run_id: "test-run",
      dataset_version: "7",
      manifest_source: { value: "default", kind: "file" },
      loaded_at: new Date().toISOString(),
    }),
  ),
  http.post("/api/predict", () => HttpResponse.json(mockPrediction)),
];

export const server = setupServer(...handlers);

export { http, HttpResponse, mockPrediction };
