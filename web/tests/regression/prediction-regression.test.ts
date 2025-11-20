import fs from "node:fs";
import path from "node:path";
import { expect, it, describe } from "vitest";

import { POST as predictHandler } from "@/app/api/predict/route";

process.env.PREDICT_LOG_SILENT = "1";

const GOLDEN_PATH = path.resolve(__dirname, "../fixtures/golden_prediction.json");
const golden = JSON.parse(fs.readFileSync(GOLDEN_PATH, "utf-8"));

function toModelMap(models: Array<{ id: string; probs: { home: number; draw: number; away: number } }>) {
  const map: Record<string, { probs: { home: number; draw: number; away: number } }> = {};
  for (const model of models) {
    map[model.id] = model;
  }
  return map;
}

function expectClose(actual: number, expected: number, tol = 1e-6) {
  expect(Math.abs(actual - expected)).toBeLessThanOrEqual(tol);
}

describe("Prediction regression", () => {
  it("matches Arsenal vs Chelsea golden snapshot", async () => {
    const body = JSON.stringify({
      homeTeam: golden.fixture.home.name,
      awayTeam: golden.fixture.away.name,
      season: String(golden.fixture.season),
    });

    const response = await predictHandler(
      new Request("http://localhost/api/predict", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body,
      }),
    );
    const json = await response.json();
    expect(json.ok).toBe(true);

    if (process.env.UPDATE_GOLDEN === "1") {
      fs.writeFileSync(GOLDEN_PATH, JSON.stringify(json, null, 2));
      return;
    }

    const actualModels = toModelMap(json.models);
    const expectedModels = toModelMap(golden.models);

    for (const id of Object.keys(expectedModels)) {
      const actual = actualModels[id];
      const expected = expectedModels[id];
      expect(actual).toBeTruthy();
      expectClose(actual.probs.home, expected.probs.home);
      expectClose(actual.probs.draw, expected.probs.draw);
      expectClose(actual.probs.away, expected.probs.away);
    }

    expectClose(json.ensemble.probs.home, golden.ensemble.probs.home);
    expectClose(json.ensemble.probs.draw, golden.ensemble.probs.draw);
    expectClose(json.ensemble.probs.away, golden.ensemble.probs.away);
  });
});
