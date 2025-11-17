import { z } from "zod";

export const resourceSchema = z.object({
  id: z.string(),
  path: z.string(),
  local_path: z.string().optional(),
  uri: z.string().optional(),
  format: z.string().optional(),
  sha256: z.string(),
  size_bytes: z.number(),
  view: z.string().optional(),
});

export const manifestSchema = z.object({
  run_id: z.string(),
  dataset_version: z.union([z.string(), z.number()]),
  trained_at: z.string(),
  notes: z.string().optional(),
  artefact_base_url: z.string().optional(),
  metrics: z.record(z.any()).optional(),
  models: z.array(resourceSchema).min(1),
  preprocessing: z.array(resourceSchema).default([]),
  attribution: z.array(resourceSchema).default([]),
});

export type ManifestResource = z.infer<typeof resourceSchema>;
export type Manifest = z.infer<typeof manifestSchema>;
