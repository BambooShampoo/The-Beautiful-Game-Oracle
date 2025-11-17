import { describe, expect, it, beforeEach, afterEach } from "vitest";

import { POST as predictHandler } from "@/app/api/predict/route";
import { resetModelCache } from "@/server/models/loader";
import {
  cleanupWorkspace,
  createManifestWorkspace,
} from "../helpers/test-manifest";

const workspaceDirs: string[] = [];

beforeEach(() => {
  resetModelCache();
  delete process.env.MODEL_MANIFEST_SOURCE;
  delete process.env.LOCAL_ARTEFACT_ROOT;
});

afterEach(async () => {
  resetModelCache();
  for (const dir of workspaceDirs.splice(0)) {
    await cleanupWorkspace(dir);
  }
});

async function seedManifest() {
  const workspace = await createManifestWorkspace();
  workspaceDirs.push(workspace.workspace);
  process.env.MODEL_MANIFEST_SOURCE = workspace.manifestPath;
  process.env.LOCAL_ARTEFACT_ROOT = workspace.workspace;
}

describe("predict route", () => {
  it("returns predictions for valid teams", async () => {
    await seedManifest();
    const response = await predictHandler(
      new Request("http://localhost/api/predict", {
        method: "POST",
        body: JSON.stringify({ homeTeam: "Arsenal", awayTeam: "Leeds" }),
        headers: { "content-type": "application/json" },
      }),
    );
    expect(response.status).toBe(200);
    const payload = (await response.json()) as {
      ok: boolean;
      models: Array<{ id: string }>;
      ensemble: { probs: { home: number; draw: number; away: number } };
    };
    // ensure ensemble probabilities sum to ~1 for heuristics fallback
    expect(payload.ok).toBe(true);
    expect(payload.models.length).toBeGreaterThan(0);
    const probSum = payload.ensemble.probs.home + payload.ensemble.probs.draw + payload.ensemble.probs.away;
    expect(Math.abs(probSum - 1)).toBeLessThan(1e-6);
  });

  it("rejects invalid teams", async () => {
    await seedManifest();
    const response = await predictHandler(
      new Request("http://localhost/api/predict", {
        method: "POST",
        body: JSON.stringify({ homeTeam: "Unknown", awayTeam: "Leeds" }),
        headers: { "content-type": "application/json" },
      }),
    );
    expect(response.status).toBe(400);
  });
});
