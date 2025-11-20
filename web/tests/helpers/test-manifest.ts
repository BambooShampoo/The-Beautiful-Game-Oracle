import crypto from "node:crypto";
import fs from "node:fs";
import { promises as fsp } from "node:fs";
import os from "node:os";
import path from "node:path";

type ManifestSeedOptions = {
  runId?: string;
  datasetVersion?: string;
  includeLocalModel?: boolean;
  modelEntryOverrides?: Partial<Record<string, unknown>>;
};

export async function createManifestWorkspace(
  options: ManifestSeedOptions = {},
) {
  const workspace = await fsp.mkdtemp(path.join(os.tmpdir(), "oracle-web-"));
  const modelRelPath = "models/performance/model.json";
  const modelAbsPath = path.join(workspace, modelRelPath);
  const includeLocalModel = options.includeLocalModel ?? true;

  if (includeLocalModel) {
    await fsp.mkdir(path.dirname(modelAbsPath), { recursive: true });
    const payload = Buffer.from(JSON.stringify({ weights: [1, 2, 3] }));
    await fsp.writeFile(modelAbsPath, payload);
  }

  const manifest = {
    run_id: options.runId ?? "test-run",
    dataset_version: options.datasetVersion ?? "7",
    trained_at: "2024-05-20T00:00:00Z",
    models: [
      {
        id: "performance_dense",
        format: "tfjs",
        path: modelRelPath,
        local_path: modelRelPath,
        uri: "https://example.com/models/performance/model.json",
        sha256: includeLocalModel
          ? sha256OfFile(modelAbsPath)
          : "0".repeat(64),
        size_bytes: includeLocalModel ? fileSize(modelAbsPath) : 0,
        ...options.modelEntryOverrides,
      },
    ],
    preprocessing: [],
    attribution: [],
  };

  const manifestPath = path.join(workspace, "manifest.json");
  await fsp.writeFile(manifestPath, JSON.stringify(manifest, null, 2));

  return {
    workspace,
    manifestPath,
    modelPath: includeLocalModel ? modelAbsPath : null,
  };
}

function sha256OfFile(filePath: string) {
  const buffer = fs.readFileSync(filePath);
  return crypto.createHash("sha256").update(buffer).digest("hex");
}

function fileSize(filePath: string) {
  const stats = fs.statSync(filePath);
  return stats.size;
}

export async function cleanupWorkspace(dir: string | null) {
  if (!dir) return;
  await fsp.rm(dir, { recursive: true, force: true });
}
