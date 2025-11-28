"use server";

import { NextResponse } from "next/server";

import { getTeamProfile } from "@/data/teamMetadata";
import {
  getLatestSeason,
  getTeamCache,
  TeamCacheEntry,
} from "@/server/predict/dataset-store";

type ApiTeam = TeamCacheEntry & {
  crest: string | null;
  aliases: string[];
};

export async function GET(request: Request) {
  try {
    const url = new URL(request.url);
    const league = url.searchParams.get("league") ?? "EPL";
    const seasonParam = url.searchParams.get("season");
    const season = seasonParam ?? getLatestSeason();
    const cache = getTeamCache(league, season);
    const teams: ApiTeam[] = cache.teams.map((team) => {
      const profile = getTeamProfile(team.canonical);
      return {
        ...team,
        crest: profile?.crest ?? null,
        aliases: profile?.aliases ?? [team.name],
      };
    });
    return NextResponse.json({
      ok: true,
      league,
      season: cache.season,
      teams,
    });
  } catch (err) {
    console.error("[API] /api/teams error:", err);
    // Debugging info for Vercel logs
    try {
      const fs = require("node:fs");
      const path = require("node:path");
      const cwd = process.cwd();
      console.log("CWD:", cwd);
      console.log("Public dir exists?", fs.existsSync(path.join(cwd, "public")));
      console.log("Public/data dir exists?", fs.existsSync(path.join(cwd, "public", "data")));
      if (fs.existsSync(path.join(cwd, "public", "data"))) {
        console.log("Public/data contents:", fs.readdirSync(path.join(cwd, "public", "data")));
      }
    } catch (debugErr) {
      console.error("Debug logging failed:", debugErr);
    }

    return NextResponse.json(
      {
        ok: false,
        error: (err as Error).message,
        stack: (err as Error).stack,
      },
      { status: 500 },
    );
  }
}
