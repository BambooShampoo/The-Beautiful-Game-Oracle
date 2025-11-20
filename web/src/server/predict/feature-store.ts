import {
  FixtureContext,
  FixtureFeatureVector,
} from "@/server/predict/types";
import {
  getFixtureRow,
  getLatestSeason,
  getTeamCache,
  type TeamCachePayload,
} from "@/server/predict/dataset-store";

// buildFixtureFeatures mirrors the Python feature_store so the API and CLI stay in sync.

export type FixtureFeatures = {
  context: FixtureContext;
  vector: FixtureFeatureVector;
};

export function buildFixtureFeatures(
  homeName: string,
  awayName: string,
  season?: string,
  datasetVersion?: string | number | null,
): FixtureFeatures {
  if (homeName.trim().toLowerCase() === awayName.trim().toLowerCase()) {
    throw new Error("Home and away teams must be different.");
  }
  const resolvedSeason = season ?? getLatestSeason(datasetVersion);
  const roster = getTeamCache("EPL", resolvedSeason, datasetVersion);
  const resolvedHome = resolveTeamName(homeName, roster);
  const resolvedAway = resolveTeamName(awayName, roster);
  const fixtureRow = getFixtureRow(resolvedSeason, resolvedHome, resolvedAway, datasetVersion);
  const vector: FixtureFeatureVector = {
    attGap: 0,
    defGap: 0,
    xgGap: 0,
    xgDefGap: 0,
    pointsGap: 0,
    wageGap: 0,
    netSpendGap: 0,
    valuationGap: 0,
    marketEdge: 0,
    volatility: 0,
    homeForm: 0,
    awayForm: 0,
    ...fixtureRow.values,
  };
  vector.attGap = vector.attGap ?? (vector.att_gap_avg5 ?? 0);
  vector.defGap = vector.defGap ?? (vector.def_gap_avg5 ?? 0);
  vector.xgGap = vector.xgGap ?? (vector.xg_att_gap_avg5 ?? 0);
  vector.xgDefGap = vector.xgDefGap ?? (vector.xg_def_gap_avg5 ?? 0);
  vector.pointsGap = vector.pointsGap ?? (vector.points_gap_avg5 ?? 0);
  vector.marketEdge = vector.marketEdge ?? (vector.prob_edge ?? 0);
  vector.volatility = vector.volatility ?? (vector.goal_diff_std_gap5 ?? 0);
  vector.wageGap = vector.wageGap ?? 0;
  vector.netSpendGap = vector.netSpendGap ?? 0;
  vector.valuationGap = vector.valuationGap ?? 0;
  vector.homeForm = vector.homeForm ?? (vector.home_points_avg5 ?? 0);
  vector.awayForm = vector.awayForm ?? (vector.away_points_avg5 ?? 0);
  fillMissingDerived(vector);
  const context: FixtureContext = {
    season: fixtureRow.season,
    home: buildTeamContext(fixtureRow.home, fixtureRow.league),
    away: buildTeamContext(fixtureRow.away, fixtureRow.league),
  };

  return { context, vector };
}

function resolveTeamName(input: string, roster: TeamCachePayload) {
  const normalized = input.trim().toLowerCase();
  const slugged = normalized.replace(/[^a-z0-9]+/g, "_").replace(/^_+|_+$/g, "");
  const match =
    roster.teams.find((team) => team.canonical === slugged) ??
    roster.teams.find((team) => team.canonical === normalized) ??
    roster.teams.find((team) => team.name.toLowerCase() === normalized) ??
    roster.teams.find((team) => team.shortName.toLowerCase() === normalized);
  return match?.name ?? input;
}

function buildTeamContext(name: string, league: string) {
  return {
    canonical: slugify(name),
    name,
    shortName: name.slice(0, 3).toUpperCase(),
    crest: "",
    league,
  };
}

function slugify(value: string) {
  return value.toLowerCase().replace(/[^a-z0-9]+/g, "_");
}

function fillMissingDerived(vector: FixtureFeatureVector) {
  const safeGap = (value: number | undefined) => (typeof value === "number" ? value : 0);
  if (vector.shot_vol_gap_avg5 === undefined) {
    vector.shot_vol_gap_avg5 =
      safeGap(vector.home_shots_for_avg5) - safeGap(vector.away_shots_for_avg5);
  }
  if (vector.shot_suppress_gap_avg5 === undefined) {
    vector.shot_suppress_gap_avg5 =
      safeGap(vector.away_shots_allowed_avg5) - safeGap(vector.home_shots_allowed_avg5);
  }
  if (vector.log_shot_ratio_avg5 === undefined) {
    const EPS = 1e-3;
    const ratio = Math.log(
      (safeGap(vector.home_shots_for_avg5) + EPS) /
        (safeGap(vector.away_shots_for_avg5) + EPS),
    );
    vector.log_shot_ratio_avg5 = Number.isFinite(ratio) ? ratio : 0;
  }
  if (vector.shots_tempo_avg5 === undefined) {
    vector.shots_tempo_avg5 =
      (safeGap(vector.home_shots_for_avg5) + safeGap(vector.away_shots_for_avg5)) / 2;
  }
}
