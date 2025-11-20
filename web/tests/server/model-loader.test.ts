import path from "node:path";

import { describe, expect, it, beforeEach, afterEach } from "vitest";

import {
  ensureManifestLoaded,
  getLoaderState,
  reloadModels,
  resetModelCache,
} from "@/server/models/loader";
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
  while (workspaceDirs.length) {
    const dir = workspaceDirs.pop();
    if (dir) {
      await cleanupWorkspace(dir);
    }
  }
});

describe("model loader", () => {
  it("loads manifest from local path and resolves local model artefact", async () => {
    const workspace = await createManifestWorkspace();
    workspaceDirs.push(workspace.workspace);
    process.env.MODEL_MANIFEST_SOURCE = workspace.manifestPath;
    process.env.LOCAL_ARTEFACT_ROOT = workspace.workspace;

    await ensureManifestLoaded(true);
    const state = getLoaderState();
    expect(state.manifest?.run_id).toBe("test-run");
    expect(state.models[0]?.location?.kind).toBe("local");
    expect(state.models[0]?.location?.kind === "local"
      ? path.normalize(state.models[0].location.path)
      : null).toContain("models/performance");
  });

  it("falls back to remote uri when local artefact missing", async () => {
    const workspace = await createManifestWorkspace({
      includeLocalModel: false,
    });
    workspaceDirs.push(workspace.workspace);
    process.env.MODEL_MANIFEST_SOURCE = workspace.manifestPath;
    process.env.LOCAL_ARTEFACT_ROOT = workspace.workspace;

    await ensureManifestLoaded(true);
    const state = getLoaderState();
    expect(state.models[0]?.location?.kind).toBe("remote");
    expect(
      state.models[0]?.location?.kind === "remote"
        ? state.models[0].location.uri
        : null,
    ).toContain("https://example.com");
  });

  it("reloads manifest from disk when invoked explicitly", async () => {
    const workspace = await createManifestWorkspace({ runId: "initial" });
    workspaceDirs.push(workspace.workspace);
    process.env.MODEL_MANIFEST_SOURCE = workspace.manifestPath;
    process.env.LOCAL_ARTEFACT_ROOT = workspace.workspace;

    await ensureManifestLoaded(true);
    const firstState = getLoaderState();
    expect(firstState.manifest?.run_id).toBe("initial");

    const second = await createManifestWorkspace({ runId: "second" });
    workspaceDirs.push(second.workspace);
    process.env.MODEL_MANIFEST_SOURCE = second.manifestPath;
    process.env.LOCAL_ARTEFACT_ROOT = second.workspace;

    await reloadModels();
    const secondState = getLoaderState();
    expect(secondState.manifest?.run_id).toBe("second");
  });

  it("loads default manifest when env not set but fallback exists", async () => {
    const state = await ensureManifestLoaded(true);
    expect(state.manifestSource).toContain("public/fixtures/mock_manifest.json");
    expect(state.models.length).toBeGreaterThan(0);
  });
});
