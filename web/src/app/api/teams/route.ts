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
}
