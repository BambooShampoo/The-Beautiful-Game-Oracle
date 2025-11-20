"use server";

import { NextResponse } from "next/server";
import { z } from "zod";

import { getLoaderState } from "@/server/models/loader";
import { logPredictFailure, logPredictSuccess } from "@/server/metrics/logger";
import { buildFixtureFeatures } from "@/server/predict/feature-store";
import { runModelPredictions } from "@/server/predict/model-runner";

const requestSchema = z.object({
  homeTeam: z.string(),
  awayTeam: z.string(),
  season: z.string().optional(),
});

export async function POST(req: Request) {
  const startedAt = Date.now();
  let parsedBody: { homeTeam: string; awayTeam: string } | null = null;
  try {
    const json = await req.json();
    const body = requestSchema.parse(json);
    parsedBody = body;
    const manifest = getLoaderState().manifest;
    const fixtureFeatures = buildFixtureFeatures(
      body.homeTeam,
      body.awayTeam,
      body.season,
      manifest?.dataset_version,
    );
    const { predictions, ensemble } = await runModelPredictions(
      fixtureFeatures.vector,
    );
    logPredictSuccess({
      home: body.homeTeam,
      away: body.awayTeam,
      runId: manifest?.run_id,
      datasetVersion: manifest?.dataset_version,
      durationMs: Date.now() - startedAt,
    });
    return NextResponse.json({
      ok: true,
      fixture: fixtureFeatures.context,
      features: fixtureFeatures.vector,
      models: predictions,
      ensemble,
    });
  } catch (error) {
    console.error("Predict route error:", error);
    const message = error instanceof z.ZodError
      ? error.issues.map((issue) => issue.message).join(", ")
      : (error as Error).message;
    logPredictFailure({
      home: parsedBody?.homeTeam ?? "unknown",
      away: parsedBody?.awayTeam ?? "unknown",
      error: message,
      runId: getLoaderState().manifest?.run_id,
      datasetVersion: getLoaderState().manifest?.dataset_version,
    });
    if (error instanceof z.ZodError) {
      return NextResponse.json(
        { ok: false, error: message },
        { status: 400 },
      );
    }
    return NextResponse.json(
      { ok: false, error: message },
      { status: 400 },
    );
  }
}
