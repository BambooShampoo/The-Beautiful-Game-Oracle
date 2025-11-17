"use server";

import { NextResponse } from "next/server";

import { getReloadToken } from "@/config/env";
import { reloadModels } from "@/server/models/loader";

function extractToken(request: Request) {
  const header = request.headers.get("x-reload-token");
  if (header) return header;
  const authHeader = request.headers.get("authorization");
  if (authHeader?.startsWith("Bearer ")) {
    return authHeader.slice("Bearer ".length);
  }
  const url = new URL(request.url);
  return url.searchParams.get("token");
}

export async function POST(request: Request) {
  try {
    const configuredToken = getReloadToken();
    if (!configuredToken) {
      return NextResponse.json(
        { ok: false, error: "Reload token not configured" },
        { status: 501 },
      );
    }

    const providedToken = extractToken(request);
    if (!providedToken || providedToken !== configuredToken) {
      return NextResponse.json(
        { ok: false, error: "Unauthorized" },
        { status: 401 },
      );
    }

    const state = await reloadModels();
    return NextResponse.json({
      ok: true,
      run_id: state.manifest?.run_id ?? null,
      reloaded_at: state.loadedAt?.toISOString() ?? null,
      models: state.models.length,
    });
  } catch (error) {
    console.error("Reload endpoint error:", error);
    return NextResponse.json(
      { ok: false, error: (error as Error).message },
      { status: 500 },
    );
  }
}
