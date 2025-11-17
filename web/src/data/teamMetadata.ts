export type TeamMetadata = {
  canonical: string;
  name: string;
  shortName: string;
  crest: string;
  aliases: string[];
  league: string;
  financial: {
    wageBill: number; // millions GBP
    netSpend: number; // millions GBP (positive = spend)
    valuation: number; // millions GBP
  };
  market: {
    impliedStrength: number; // baseline win probability proxy
  };
};

const TEAMS: TeamMetadata[] = [
  {
    canonical: "arsenal",
    name: "Arsenal",
    shortName: "ARS",
    crest:
      "https://upload.wikimedia.org/wikipedia/en/5/53/Arsenal_FC.svg",
    aliases: ["arsenal", "arsenal fc", "the gunners"],
    league: "EPL",
    financial: {
      wageBill: 220,
      netSpend: -35,
      valuation: 2100,
    },
    market: {
      impliedStrength: 0.62,
    },
  },
  {
    canonical: "chelsea",
    name: "Chelsea",
    shortName: "CHE",
    crest:
      "https://upload.wikimedia.org/wikipedia/en/c/cc/Chelsea_FC.svg",
    aliases: ["chelsea", "chelsea fc", "the blues"],
    league: "EPL",
    financial: {
      wageBill: 260,
      netSpend: 130,
      valuation: 2400,
    },
    market: {
      impliedStrength: 0.55,
    },
  },
  {
    canonical: "manchester_city",
    name: "Manchester City",
    shortName: "MCI",
    crest:
      "https://upload.wikimedia.org/wikipedia/en/e/eb/Manchester_City_FC_badge.svg",
    aliases: [
      "manchester city",
      "man city",
      "mcfc",
      "manchester city fc",
    ],
    league: "EPL",
    financial: {
      wageBill: 300,
      netSpend: 40,
      valuation: 3200,
    },
    market: {
      impliedStrength: 0.72,
    },
  },
  {
    canonical: "liverpool",
    name: "Liverpool",
    shortName: "LIV",
    crest:
      "https://upload.wikimedia.org/wikipedia/en/0/0c/Liverpool_FC.svg",
    aliases: ["liverpool", "lfc", "liverpool fc", "the reds"],
    league: "EPL",
    financial: {
      wageBill: 240,
      netSpend: -10,
      valuation: 2900,
    },
    market: {
      impliedStrength: 0.64,
    },
  },
];

const aliasIndex = new Map<string, TeamMetadata>();
const canonicalIndex = new Map<string, TeamMetadata>();
for (const team of TEAMS) {
  canonicalIndex.set(normalize(team.canonical), team);
  for (const alias of team.aliases) {
    aliasIndex.set(normalize(alias), team);
  }
  aliasIndex.set(normalize(team.name), team);
  aliasIndex.set(normalize(team.shortName), team);
  aliasIndex.set(normalize(team.canonical), team);
}

function normalize(input: string) {
  return input.trim().toLowerCase();
}

export function listTeams() {
  return TEAMS;
}

export function findTeamByName(name: string) {
  return aliasIndex.get(normalize(name)) ?? null;
}

export function findTeamByCanonical(canonical: string) {
  return canonicalIndex.get(normalize(canonical)) ?? null;
}

export function getTeamProfile(canonical: string) {
  return findTeamByCanonical(canonical);
}

export function searchTeam(query: string) {
  const normalized = normalize(query);
  if (!normalized) return null;
  return (
    aliasIndex.get(normalized) ??
    TEAMS.find(
      (team) =>
        team.name.toLowerCase().includes(normalized) ||
        team.canonical.includes(normalized) ||
        team.aliases.some((alias) => normalize(alias).includes(normalized)),
    ) ??
    null
  );
}
