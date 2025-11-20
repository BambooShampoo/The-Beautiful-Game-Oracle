from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd
import pytest

from pipelines.feature_store import FeatureStore

DATASET_PATH = Path("understat_data/Dataset_Version_7.csv")
SAMPLE_FIXTURE = {
    "season": "2025",
    "home": "Arsenal",
    "away": "Leeds",
    "match_id": 28793,
}


@pytest.mark.skipif(not DATASET_PATH.exists(), reason="Dataset_Version_7.csv missing")
def test_prob_edge_matches_raw_dataset():
    raw_df = pd.read_csv(
        DATASET_PATH,
        parse_dates=["match_datetime_utc", "match_date"],
    ).sort_values("match_datetime_utc")
    match_row = raw_df.loc[raw_df["match_id"] == SAMPLE_FIXTURE["match_id"]].iloc[0]
    expected = float(match_row["forecast_home_win"] - match_row["forecast_away_win"])
    store = FeatureStore(dataset_version="7", cache_path=None)
    fixture = store.get_fixture(SAMPLE_FIXTURE["season"], SAMPLE_FIXTURE["home"], SAMPLE_FIXTURE["away"])
    assert fixture.features["prob_edge"] == pytest.approx(expected)


@pytest.mark.skipif(not DATASET_PATH.exists(), reason="Dataset_Version_7.csv missing")
def test_recent_games_fraction_matches_manual():
    raw_df = pd.read_csv(
        DATASET_PATH,
        parse_dates=["match_datetime_utc", "match_date"],
    ).sort_values("match_datetime_utc")
    window = 5
    home_counts = (
        raw_df.groupby(["season", "home_team_name"], sort=False).cumcount().clip(upper=window)
    )
    match_row = raw_df.loc[raw_df["match_id"] == SAMPLE_FIXTURE["match_id"]]
    assert not match_row.empty
    idx = match_row.index[0]
    expected = float(home_counts.loc[idx]) / window
    store = FeatureStore(dataset_version="7", cache_path=None)
    fixture = store.get_fixture(SAMPLE_FIXTURE["season"], SAMPLE_FIXTURE["home"], SAMPLE_FIXTURE["away"])
    assert fixture.features["home_recent_games_frac"] == pytest.approx(expected)


@pytest.mark.skipif(not DATASET_PATH.exists(), reason="Dataset_Version_7.csv missing")
def test_feature_cache_persists_vectors(tmp_path: Path):
    cache_path = tmp_path / "fixture_cache.sqlite"
    store = FeatureStore(dataset_version="7", cache_path=cache_path)
    fixture = store.get_fixture(SAMPLE_FIXTURE["season"], SAMPLE_FIXTURE["home"], SAMPLE_FIXTURE["away"])
    assert "prob_edge" in fixture.features

    season_key = SAMPLE_FIXTURE["season"].strip().lower()
    home_key = SAMPLE_FIXTURE["home"].strip().lower()
    away_key = SAMPLE_FIXTURE["away"].strip().lower()
    with sqlite3.connect(cache_path) as conn:
        payload = conn.execute(
            "SELECT payload FROM feature_cache WHERE dataset_version=? AND season=? AND home=? AND away=?",
            (store.dataset_version, season_key, home_key, away_key),
        ).fetchone()
    assert payload is not None, "Feature row missing from cache"
