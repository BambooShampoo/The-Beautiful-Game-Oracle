"use client";

import { useEffect, useState } from "react";

export type TeamOption = {
  canonical: string;
  name: string;
  shortName: string;
  league: string;
  crest: string | null;
  aliases: string[];
};

// useTeamOptions fetches the cached team roster for the requested league and exposes loading/error state.
type TeamResponse = {
  ok: boolean;
  league: string;
  season: string;
  teams: TeamOption[];
  error?: string;
};

export function useTeamOptions(league = "EPL") {
  const [teams, setTeams] = useState<TeamOption[]>([]);
  const [season, setSeason] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      setLoading(true);
      setError(null);
      try {
        const response = await fetch(`/api/teams?league=${encodeURIComponent(league)}`);
        const payload = (await response.json()) as TeamResponse;
        if (!response.ok || !payload.ok) {
          throw new Error(payload.error ?? "Failed to load teams.");
        }
        if (!cancelled) {
          setTeams(payload.teams);
          setSeason(payload.season);
          setLoading(false);
        }
      } catch (err) {
        if (!cancelled) {
          setError((err as Error).message);
          setTeams([]);
          setSeason(null);
          setLoading(false);
        }
      }
    }
    load();
    return () => {
      cancelled = true;
    };
  }, [league]);

  return { teams, season, loading, error };
}
