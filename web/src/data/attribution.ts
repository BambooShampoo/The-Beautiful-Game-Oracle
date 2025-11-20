export type FeatureContribution = {
  feature: string;
  value: number;
  description: string;
};

export type AttributionView = {
  topContributors: FeatureContribution[];
  negativeContributors: FeatureContribution[];
  loo: Array<{
    signal: string;
    delta: number;
  }>;
};

export const attributionViews: Record<string, AttributionView> = {
  performance: {
    topContributors: [
      {
        feature: "attGap",
        value: 0.41,
        description: "Home attack vs away attack rolling delta.",
      },
      {
        feature: "xgGap",
        value: 0.35,
        description: "xG strength advantage using last-5 matches.",
      },
      {
        feature: "pointsGap",
        value: 0.29,
        description: "Recent points per match differential.",
      },
    ],
    negativeContributors: [
      {
        feature: "volatility",
        value: -0.18,
        description: "High variance dampens model confidence.",
      },
      {
        feature: "defGap",
        value: -0.11,
        description: "Away defence trending better than home attack.",
      },
    ],
    loo: [
      { signal: "Attack delta", delta: -0.067 },
      { signal: "xG gap", delta: -0.044 },
      { signal: "Volatility", delta: -0.012 },
    ],
  },
  financial: {
    topContributors: [
      {
        feature: "valuationGap",
        value: 0.32,
        description: "Market value ratio between the clubs.",
      },
      {
        feature: "wageGap",
        value: 0.21,
        description: "Wage bill difference per 50M GBP.",
      },
    ],
    negativeContributors: [
      {
        feature: "netSpendGap",
        value: -0.08,
        description: "Recent net spend favors the away side.",
      },
    ],
    loo: [
      { signal: "Valuation", delta: -0.041 },
      { signal: "Wages", delta: -0.018 },
      { signal: "Net spend", delta: -0.006 },
    ],
  },
  market: {
    topContributors: [
      {
        feature: "marketEdge",
        value: 0.27,
        description: "Implied probability delta vs visitor.",
      },
      {
        feature: "entropy",
        value: 0.12,
        description: "Book odds concentration.",
      },
    ],
    negativeContributors: [
      {
        feature: "liveUnderdogBias",
        value: -0.05,
        description: "Market signals lean to the away side.",
      },
    ],
    loo: [
      { signal: "Edge", delta: -0.031 },
      { signal: "Entropy", delta: -0.009 },
      { signal: "Volatility", delta: -0.004 },
    ],
  },
};
