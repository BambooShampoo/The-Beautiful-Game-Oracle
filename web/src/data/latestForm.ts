import { findTeamByName, listTeams } from "@/data/teamMetadata";

export type FormSnapshot = {
  canonical: string;
  season: string;
  matches: number;
  goalsForAvg5: number;
  goalsAgainstAvg5: number;
  xgForAvg5: number;
  xgAgainstAvg5: number;
  pointsAvg5: number;
  marketHomeProb: number;
  volatility: number;
};

const DEFAULT_SEASON = "2025";

const FORM_DATA: FormSnapshot[] = [
  {
    canonical: "arsenal",
    season: DEFAULT_SEASON,
    matches: 5,
    goalsForAvg5: 2.2,
    goalsAgainstAvg5: 0.8,
    xgForAvg5: 2.4,
    xgAgainstAvg5: 0.9,
    pointsAvg5: 2.4,
    marketHomeProb: 0.62,
    volatility: 0.32,
  },
  {
    canonical: "chelsea",
    season: DEFAULT_SEASON,
    matches: 5,
    goalsForAvg5: 1.6,
    goalsAgainstAvg5: 1.3,
    xgForAvg5: 1.8,
    xgAgainstAvg5: 1.2,
    pointsAvg5: 1.7,
    marketHomeProb: 0.55,
    volatility: 0.46,
  },
  {
    canonical: "manchester_city",
    season: DEFAULT_SEASON,
    matches: 5,
    goalsForAvg5: 2.5,
    goalsAgainstAvg5: 0.7,
    xgForAvg5: 2.6,
    xgAgainstAvg5: 0.8,
    pointsAvg5: 2.5,
    marketHomeProb: 0.71,
    volatility: 0.28,
  },
  {
    canonical: "liverpool",
    season: DEFAULT_SEASON,
    matches: 5,
    goalsForAvg5: 2.3,
    goalsAgainstAvg5: 1.0,
    xgForAvg5: 2.2,
    xgAgainstAvg5: 1.1,
    pointsAvg5: 2.2,
    marketHomeProb: 0.64,
    volatility: 0.35,
  },
];

const formIndex = new Map<string, FormSnapshot>();
for (const snapshot of FORM_DATA) {
  formIndex.set(makeKey(snapshot.canonical, snapshot.season), snapshot);
}

function makeKey(canonical: string, season: string) {
  return `${canonical}::${season}`;
}

function buildFallbackSnapshot(canonical: string, season: string): FormSnapshot {
  const team = findTeamByName(canonical) ?? listTeams()[0];
  return {
    canonical: team?.canonical ?? canonical,
    season,
    matches: 0,
    goalsForAvg5: 1.5,
    goalsAgainstAvg5: 1.5,
    xgForAvg5: 1.6,
    xgAgainstAvg5: 1.6,
    pointsAvg5: 1.5,
    marketHomeProb: 0.5,
    volatility: 0.5,
  };
}

export function getFormSnapshot(
  canonical: string,
  season: string = DEFAULT_SEASON,
) {
  return formIndex.get(makeKey(canonical, season)) ?? buildFallbackSnapshot(canonical, season);
}

export { DEFAULT_SEASON };
