import fs from "node:fs";
import path from "node:path";

import { expect, test } from "vitest";

import { getFixtureRow } from "@/server/predict/dataset-store";

const DATASET_PATH = path.resolve(process.cwd(), "../understat_data/Dataset_Version_7.csv");
const fixtureUrl = new URL("../fixtures/fixture_palace_arsenal.json", import.meta.url);
const EXPECTED_FEATURES = JSON.parse(fs.readFileSync(fixtureUrl, "utf-8")) as Record<string, number>;

const maybeTest = fs.existsSync(DATASET_PATH) ? test : test.skip;

maybeTest("dataset store derives notebook-aligned features", () => {
  const row = getFixtureRow("2022", "Crystal Palace", "Arsenal", "7");
  const values = row.values;
  expect(values.home_recent_games_frac).toBeCloseTo(EXPECTED_FEATURES.home_recent_games_frac);
  expect(values.away_recent_games_frac).toBeCloseTo(EXPECTED_FEATURES.away_recent_games_frac);
  expect(values.shot_vol_gap_avg5).toBeCloseTo(EXPECTED_FEATURES.shot_vol_gap_avg5);
  expect(values.shot_suppress_gap_avg5).toBeCloseTo(EXPECTED_FEATURES.shot_suppress_gap_avg5);
  expect(values.log_shot_ratio_avg5).toBeCloseTo(EXPECTED_FEATURES.log_shot_ratio_avg5);
  expect(values.shot_volume_gap_avg3_season_z).toBeCloseTo(EXPECTED_FEATURES.shot_volume_gap_avg3_season_z);
  expect(values.points_gap_avg5).toBeCloseTo(EXPECTED_FEATURES.points_gap_avg5);
  expect(values.xg_att_gap_avg5).toBeCloseTo(EXPECTED_FEATURES.xg_att_gap_avg5);
  expect(values.prob_edge).toBeCloseTo(EXPECTED_FEATURES.prob_edge);
  expect(values.shots_tempo_avg3_season_z).toBeCloseTo(EXPECTED_FEATURES.shots_tempo_avg3_season_z);
});
