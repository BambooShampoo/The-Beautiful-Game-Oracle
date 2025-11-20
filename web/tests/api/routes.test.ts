import { describe, expect, it, beforeEach, afterEach } from "vitest";

import { POST as reloadHandler } from "@/app/api/reload/route";
import { GET as statusHandler } from "@/app/api/status/route";
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
  process.env.RELOAD_TOKEN = "test-token";
});

afterEach(async () => {
  resetModelCache();
  for (const dir of workspaceDirs.splice(0)) {
    await cleanupWorkspace(dir);
  }
});

describe("status route", () => {
  it("returns manifest summary", async () => {
    const workspace = await createManifestWorkspace();
    workspaceDirs.push(workspace.workspace);
    process.env.MODEL_MANIFEST_SOURCE = workspace.manifestPath;
    process.env.LOCAL_ARTEFACT_ROOT = workspace.workspace;

    const response = await statusHandler();
    expect(response.status).toBe(200);
    const payload = (await response.json()) as Record<string, unknown>;
    expect(payload["run_id"]).toBe("test-run");
    expect(payload["models"]).toBeTruthy();
  });
});

describe("reload route", () => {
  it("reloads when valid token is provided", async () => {
    const workspace = await createManifestWorkspace({ runId: "initial" });
    workspaceDirs.push(workspace.workspace);
    process.env.MODEL_MANIFEST_SOURCE = workspace.manifestPath;
    process.env.LOCAL_ARTEFACT_ROOT = workspace.workspace;

    const response = await reloadHandler(
      new Request("http://localhost/api/reload", {
        method: "POST",
        headers: {
          "x-reload-token": "test-token",
        },
      }),
    );
    expect(response.status).toBe(200);
    const payload = (await response.json()) as Record<string, unknown>;
    expect(payload["ok"]).toBe(true);
  });

  it("rejects invalid tokens", async () => {
    const workspace = await createManifestWorkspace({ runId: "initial" });
    workspaceDirs.push(workspace.workspace);
    process.env.MODEL_MANIFEST_SOURCE = workspace.manifestPath;
    process.env.LOCAL_ARTEFACT_ROOT = workspace.workspace;

    const response = await reloadHandler(
      new Request("http://localhost/api/reload", {
        method: "POST",
        headers: {
          "x-reload-token": "wrong",
        },
      }),
    );
    expect(response.status).toBe(401);
  });
});
