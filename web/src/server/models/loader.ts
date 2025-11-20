import { promises as fs } from "node:fs";
import path from "node:path";

import { getLocalArtefactRoot, getManifestSource } from "@/config/env";
import {
  Manifest,
  ManifestResource,
  manifestSchema,
} from "@/server/models/manifest-schema";

const HTTP_REGEX = /^https?:\/\//i;

export type ResourceLocation =
  | { kind: "local"; path: string }
  | { kind: "remote"; uri: string };

export type ResourceHandle = {
  id: string;
  entry: ManifestResource;
  location: ResourceLocation | null;
};

type LoaderState = {
  manifest: Manifest | null;
  manifestSource: string | null;
  manifestKind: "file" | "remote" | null;
  manifestDir: string | null;
  models: ResourceHandle[];
  preprocessing: ResourceHandle[];
  attribution: ResourceHandle[];
  loadedAt: Date | null;
  errors: string[];
};

let loaderState: LoaderState = {
  manifest: null,
  manifestSource: null,
  manifestKind: null,
  manifestDir: null,
  models: [],
  preprocessing: [],
  attribution: [],
  loadedAt: null,
  errors: [],
};

function resetState() {
  loaderState = {
    manifest: null,
    manifestSource: null,
    manifestKind: null,
    manifestDir: null,
    models: [],
    preprocessing: [],
    attribution: [],
    loadedAt: null,
    errors: [],
  };
}

export function resetModelCache() {
  resetState();
}

export function getLoaderState() {
  return loaderState;
}

export async function ensureManifestLoaded(force = false) {
  if (loaderState.manifest && !force) {
    return loaderState;
  }

  const source = getManifestSource();
  const isRemote = HTTP_REGEX.test(source);

  const parsed = isRemote
    ? await fetchRemoteManifest(source)
    : await readLocalManifest(source);

  const manifestDir = parsed.manifestDir;
  const localRoots = buildLocalRoots(manifestDir);

  const [models, preprocessing, attribution] = await Promise.all([
    hydrateResources(parsed.manifest.models, localRoots, parsed.manifest),
    hydrateResources(parsed.manifest.preprocessing ?? [], localRoots, parsed.manifest),
    hydrateResources(parsed.manifest.attribution ?? [], localRoots, parsed.manifest),
  ]);
  const errors = [...models.errors, ...preprocessing.errors, ...attribution.errors];

  loaderState = {
    manifest: parsed.manifest,
    manifestSource: parsed.source,
    manifestKind: parsed.kind,
    manifestDir,
    models: models.handles,
    preprocessing: preprocessing.handles,
    attribution: attribution.handles,
    loadedAt: new Date(),
    errors,
  };
  return loaderState;
}

export async function reloadModels() {
  return ensureManifestLoaded(true);
}

async function fetchRemoteManifest(source: string) {
  const response = await fetch(source);
  if (!response.ok) {
    throw new Error(`Failed to fetch manifest (${response.status} ${response.statusText})`);
  }
  const text = await response.text();
  return {
    manifest: parseManifest(text),
    source,
    kind: "remote" as const,
    manifestDir: null,
  };
}

async function readLocalManifest(inputPath: string) {
  const resolved = path.resolve(inputPath);
  const text = await fs.readFile(resolved, "utf-8");
  return {
    manifest: parseManifest(text),
    source: resolved,
    kind: "file" as const,
    manifestDir: path.dirname(resolved),
  };
}

function parseManifest(text: string): Manifest {
  const data = JSON.parse(text);
  return manifestSchema.parse(data);
}

function buildLocalRoots(manifestDir: string | null) {
  const roots = new Set<string>();
  roots.add(getLocalArtefactRoot());
  roots.add(process.cwd());
  if (manifestDir) {
    roots.add(manifestDir);
  }
  return Array.from(roots);
}

async function hydrateResources(
  entries: ManifestResource[],
  localRoots: string[],
  manifest: Manifest,
) {
  const handles: ResourceHandle[] = [];
  const errors: string[] = [];
  for (const entry of entries) {
    const location = await resolveResourceLocation(entry, localRoots, manifest);
    if (!location) {
      errors.push(
        `Failed to resolve artefact '${entry.id}'. Provide LOCAL_ARTEFACT_ROOT or check manifest paths.`,
      );
    }
    handles.push({ id: entry.id, entry, location });
  }
  return { handles, errors };
}

async function resolveResourceLocation(
  entry: ManifestResource,
  localRoots: string[],
  manifest: Manifest,
): Promise<ResourceLocation | null> {
  const localPath = await findLocalPath(entry, localRoots);
  if (localPath) {
    return { kind: "local", path: localPath };
  }
  const remoteUri = resolveRemoteUri(entry, manifest);
  if (remoteUri) {
    return { kind: "remote", uri: remoteUri };
  }
  return null;
}

async function findLocalPath(entry: ManifestResource, localRoots: string[]) {
  const candidates = [entry.local_path, entry.path].filter(Boolean) as string[];
  for (const candidate of candidates) {
    if (path.isAbsolute(candidate)) {
      if (await fileExists(candidate)) {
        return candidate;
      }
      continue;
    }
    for (const root of localRoots) {
      const resolved = path.resolve(root, candidate);
      if (await fileExists(resolved)) {
        return resolved;
      }
    }
  }
  return null;
}

async function fileExists(target: string) {
  try {
    await fs.access(target);
    return true;
  } catch {
    return false;
  }
}

function resolveRemoteUri(entry: ManifestResource, manifest: Manifest) {
  if (entry.uri && HTTP_REGEX.test(entry.uri)) {
    return entry.uri;
  }
  if (manifest.artefact_base_url) {
    return joinUrl(manifest.artefact_base_url, entry.path);
  }
  if (HTTP_REGEX.test(entry.path)) {
    return entry.path;
  }
  return null;
}

function joinUrl(base: string, suffix: string) {
  const sanitizedBase = base.replace(/\/+$/, "");
  const sanitizedSuffix = suffix.replace(/^\/+/, "");
  return `${sanitizedBase}/${sanitizedSuffix}`;
}
