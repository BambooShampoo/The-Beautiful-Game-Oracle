import { promises as fs } from "node:fs";

import type { ResourceHandle } from "@/server/models/loader";

export type PreprocessingBundle = {
  feature_names: string[];
  scaling?: {
    mean: number[];
    std: number[];
  };
};

const cache = new Map<string, PreprocessingBundle>();

export async function loadPreprocessing(handle: ResourceHandle | undefined) {
  if (!handle || !handle.location || handle.location.kind !== "local") {
    return null;
  }
  const cached = cache.get(handle.location.path);
  if (cached) return cached;
  const data = await fs.readFile(handle.location.path, "utf-8");
  const bundle = JSON.parse(data) as PreprocessingBundle;
  cache.set(handle.location.path, bundle);
  return bundle;
}

export function matchPreprocessing(
  model: ResourceHandle,
  preprocessingHandles: ResourceHandle[],
): ResourceHandle | undefined {
  const matches = preprocessingHandles.find((handle) => {
    if (handle.entry.id === model.id) return true;
    return handle.entry.id.startsWith(`${model.id}_`);
  });
  return matches;
}
