import fs from "node:fs";
import path from "node:path";

export function getManifestSource(): string {
  const value = process.env.MODEL_MANIFEST_SOURCE;
  if (value && value.trim().length > 0) {
    return value;
  }
  const fallback = path.resolve(process.cwd(), "./public/fixtures/mock_manifest.json");
  if (fs.existsSync(fallback)) {
    return fallback;
  }
  throw new Error(
    "MODEL_MANIFEST_SOURCE is not set and no fallback manifest was found. Provide a local file path or remote URL pointing to model_manifest.json.",
  );
}

export function getLocalArtefactRoot(): string {
  const root = process.env.LOCAL_ARTEFACT_ROOT;
  if (root && root.trim().length > 0) {
    return path.resolve(root);
  }
  return path.resolve(process.cwd(), "..");
}

export function getDatasetRoot(): string {
  const root = process.env.FEATURE_DATASET_ROOT;
  if (root && root.trim().length > 0) {
    return path.resolve(root);
  }
  return path.resolve(process.cwd(), "./public/fixtures");
}

export function getTeamCacheDir(): string {
  const dir = process.env.FEATURE_TEAM_CACHE_DIR;
  if (dir && dir.trim().length > 0) {
    return path.resolve(dir);
  }
  return path.resolve(getDatasetRoot(), "team_cache");
}

export function getReloadToken(): string | null {
  return process.env.RELOAD_TOKEN ?? null;
}

export function getFeatureDatasetVersion(): string | null {
  const value = process.env.FEATURE_DATASET_VERSION;
  if (value && value.trim().length > 0) {
    return value.trim();
  }
  return null;
}

export function getEnvSummary() {
  return {
    manifestSource: process.env.MODEL_MANIFEST_SOURCE ?? null,
    localArtefactRoot: getLocalArtefactRoot(),
    reloadTokenConfigured: Boolean(process.env.RELOAD_TOKEN),
    featureDatasetVersion: getFeatureDatasetVersion(),
  };
}
