"use server";

import { NextResponse } from "next/server";

import { getEnvSummary } from "@/config/env";
import { ensureManifestLoaded, getLoaderState } from "@/server/models/loader";

export async function GET() {
  try {
    await ensureManifestLoaded();
    const state = getLoaderState();
    return NextResponse.json({
      ok: true,
      run_id: state.manifest?.run_id ?? null,
      dataset_version: state.manifest?.dataset_version ?? null,
      trained_at: state.manifest?.trained_at ?? null,
      manifest_source: {
        value: state.manifestSource,
        kind: state.manifestKind,
      },
      loaded_at: state.loadedAt?.toISOString() ?? null,
      models: state.models.map((handle) => ({
        id: handle.id,
        format: handle.entry.format ?? null,
        location:
          handle.location?.kind === "local"
            ? { kind: "local", path: handle.location.path }
            : handle.location?.kind === "remote"
              ? { kind: "remote", uri: handle.location.uri }
              : null,
      })),
      errors: state.errors,
      env: getEnvSummary(),
    });
  } catch (error) {
    console.error("Status endpoint error:", error);
    return NextResponse.json(
      { ok: false, error: (error as Error).message },
      { status: 500 },
    );
  }
}
