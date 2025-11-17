"""Feature store mirroring notebook preprocessing for local inference.

This module owns dataset loading, feature derivation, and fixture caching so
CLI scripts and notebooks can rebuild the same feature vectors that power the
web predictions without duplicating pandas logic.
"""

from __future__ import annotations

import json
import logging
import os
import sqlite3
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd

from pipelines.notebook_catalog import (
    DEFAULT_EXPERIMENT_ROOT,
    NotebookRun,
    discover_latest_notebook_run,
    resolve_dataset_version,
)
from pipelines.team_cache import ensure_latest_team_caches

DEFAULT_DATASET_VERSION = "7"
DEFAULT_ROLLING_WINDOW = 5
CACHE_PATH = Path("understat_data") / "feature_cache.sqlite"
DATASET_TEMPLATE = "understat_data/Dataset_Version_{version}.csv"
LOGGER = logging.getLogger(__name__)
MODEL_NAMES = ("performance_dense", "momentum_policy_rl", "market_gradient_boost")

FALLBACK_MODEL_FEATURES: Dict[str, Sequence[str]] = {
    "performance_dense": [
        "home_goal_diff_std5",
        "away_goal_diff_std5",
        "goal_diff_std_gap5",
        "home_goal_diff_exp_decay",
        "away_goal_diff_exp_decay",
        "goal_diff_exp_decay_gap",
        "home_xg_diff_std5",
        "away_xg_diff_std5",
        "xg_diff_std_gap5",
        "home_xg_diff_exp_decay",
        "away_xg_diff_exp_decay",
        "xg_diff_exp_decay_gap",
        "home_shot_diff_std5",
        "away_shot_diff_std5",
        "shot_diff_std_gap5",
        "home_shot_diff_exp_decay",
        "away_shot_diff_exp_decay",
        "shot_diff_exp_decay_gap",
        "home_recent_games_frac",
        "away_recent_games_frac",
        "home_shots_for_avg5",
        "home_shots_allowed_avg5",
        "away_shots_for_avg5",
        "away_shots_allowed_avg5",
        "shot_vol_gap_avg5",
        "shot_suppress_gap_avg5",
        "log_shot_ratio_avg5",
        "shots_tempo_avg5",
        "att_gap_avg5",
        "def_gap_avg5",
        "points_gap_avg5",
        "xg_att_gap_avg5",
        "xg_def_gap_avg5",
        "log_xg_ratio_avg5",
        "home_goals_for_avg5",
        "home_goals_against_avg5",
        "away_goals_for_avg5",
        "away_goals_against_avg5",
        "elo_home_pre",
        "elo_away_pre",
        "elo_mean_pre",
        "elo_gap_pre",
        "elo_home_expectation",
        "elo_expectation_gap",
    ],
    "momentum_policy_rl": [
        "momentum_points_last3_delta_season_z",
        "momentum_points_last2_delta_season_z",
        "momentum_points_last8_delta_season_z",
        "momentum_points_pct_last3_delta_season_z",
        "momentum_goal_diff_last3_delta_season_z",
        "momentum_goal_diff_last2_delta_season_z",
        "momentum_goal_diff_last8_delta_season_z",
        "momentum_xg_diff_last3_delta_season_z",
        "momentum_xg_diff_last2_delta_season_z",
        "momentum_xg_diff_last8_delta_season_z",
        "momentum_points_exp_decay_delta_season_z",
        "momentum_xg_exp_decay_delta_season_z",
        "momentum_matches_last14_delta_season_z",
        "momentum_travel_rest_ratio_delta_season_z",
        "momentum_forecast_win_prev_delta_season_z",
        "momentum_forecast_trend_delta_season_z",
        "shot_volume_gap_avg3_season_z",
        "shot_suppress_gap_avg3_season_z",
        "shots_tempo_avg3_season_z",
        "elo_gap_pre_season_z",
        "market_vs_elo_edge",
        "form_pct_diff_last5_season_z",
        "form_diff_last5_season_z",
        "rest_diff_season_z",
        "fixture_congestion_flag_pair",
        "momentum_fixture_congestion_delta",
        "rest_reset_flag_pair",
        "match_day_index_season_z",
        "match_day_of_year_norm_season_z",
        "match_weekday_index_season_z",
    ],
    "market_gradient_boost": [
        "forecast_home_win",
        "forecast_draw",
        "forecast_away_win",
        "market_home_edge",
        "market_entropy",
        "market_logit_home",
        "market_max_prob",
        "prob_edge",
        "elo_home_pre",
        "elo_away_pre",
        "elo_mean_pre",
        "elo_gap_pre",
        "elo_home_expectation",
        "elo_expectation_gap",
        "market_vs_elo_edge",
        "match_day_index",
        "match_day_of_year_norm",
        "match_weekday_index",
    ],
}


def _normalize_name(value: str) -> str:
    return str(value).strip().lower()


def _dataset_path_from_version(version: str) -> Path:
    return Path(DATASET_TEMPLATE.format(version=version))


class FeatureOrigin(str, Enum):
    DIRECT = "direct"
    DERIVED = "derived"
    UNKNOWN = "unknown"


@dataclass
class FixtureFeatures:
    match_id: int
    home_team: str
    away_team: str
    season: str
    features: Dict[str, float]


class FeatureCache:
    """SQLite cache storing computed feature vectors per dataset version."""

    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_schema()

    def _ensure_schema(self) -> None:
        with sqlite3.connect(self.path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS feature_cache (
                    dataset_version TEXT NOT NULL,
                    season TEXT NOT NULL,
                    home TEXT NOT NULL,
                    away TEXT NOT NULL,
                    match_id INTEGER NOT NULL,
                    dataset_mtime REAL NOT NULL,
                    payload TEXT NOT NULL,
                    PRIMARY KEY (dataset_version, season, home, away)
                )
                """
            )
            conn.commit()

    def get(
        self,
        dataset_version: str,
        season: str,
        home: str,
        away: str,
        dataset_mtime: float,
    ) -> Optional[Dict[str, float]]:
        with sqlite3.connect(self.path) as conn:
            cursor = conn.execute(
                """
                SELECT payload, dataset_mtime
                FROM feature_cache
                WHERE dataset_version = ? AND season = ? AND home = ? AND away = ?
                """,
                (dataset_version, season, home, away),
            )
            row = cursor.fetchone()
        if not row:
            return None
        payload, cached_mtime = row
        if abs(cached_mtime - dataset_mtime) > 1e-6:
            return None
        return json.loads(payload)

    def set(
        self,
        dataset_version: str,
        season: str,
        home: str,
        away: str,
        dataset_mtime: float,
        match_id: int,
        features: Dict[str, float],
    ) -> None:
        with sqlite3.connect(self.path) as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO feature_cache
                (dataset_version, season, home, away, match_id, dataset_mtime, payload)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    dataset_version,
                    season,
                    home,
                    away,
                    match_id,
                    dataset_mtime,
                    json.dumps(features),
                ),
            )
            conn.commit()


class FeatureStore:
    """Loads Understat datasets and mirrors notebook feature engineering."""

    def __init__(
        self,
        *,
        dataset_version: Optional[str] = None,
        dataset_path: Optional[Path] = None,
        cache_path: Optional[Path] = CACHE_PATH,
        experiments_root: Path = DEFAULT_EXPERIMENT_ROOT,
        rolling_window: int = DEFAULT_ROLLING_WINDOW,
    ):
        notebook_run = discover_latest_notebook_run(experiments_root, model_names=MODEL_NAMES)
        env_version = os.getenv("FEATURE_DATASET_VERSION")
        self._model_features = (
            notebook_run.feature_columns if notebook_run else FALLBACK_MODEL_FEATURES
        )
        notebook_label = None
        fallback_versions = []
        if notebook_run:
            fallback_versions = notebook_run.dataset_versions
            if notebook_run.models:
                first_model = next(iter(notebook_run.models.values()))
                notebook_label = first_model.dataset_label
        explicit_version = dataset_version or env_version
        resolved_version = resolve_dataset_version(
            explicit_version,
            dataset_label=notebook_label,
            fallback_versions=fallback_versions,
        )
        if not resolved_version and dataset_path:
            resolved_version = resolve_dataset_version(
                None,
                dataset_label=_guess_version_from_name(dataset_path.name),
            )
        self.dataset_version = resolved_version or DEFAULT_DATASET_VERSION
        self.dataset_path = dataset_path or _dataset_path_from_version(self.dataset_version)
        if not self.dataset_path.exists():
            raise FileNotFoundError(
                f"Dataset not found at {self.dataset_path}. "
                "Rebuild the dataset or point FEATURE_DATASET_VERSION at an available CSV.",
            )
        self.dataset_mtime = self.dataset_path.stat().st_mtime
        self.rolling_window = rolling_window
        self._df: Optional[pd.DataFrame] = None
        self._latest_season: Optional[str] = None
        self._baseline_columns: Optional[set[str]] = None
        self._derived_columns: Optional[set[str]] = None
        self._unknown_features_logged: set[str] = set()
        self._required_features: Optional[List[str]] = None
        self.cache = FeatureCache(cache_path) if cache_path else None

    @property
    def df(self) -> pd.DataFrame:
        if self._df is None:
            parse_dates = ["match_datetime_utc", "match_date"]
            header = pd.read_csv(self.dataset_path, nrows=0)
            date_cols = [col for col in parse_dates if col in header.columns]
            df = pd.read_csv(self.dataset_path, parse_dates=date_cols)
            if "match_datetime_utc" in df.columns:
                df = df.sort_values("match_datetime_utc")
            df["season"] = df["season"].astype(str)
            df["home_team"] = df["home_team_name"]
            df["away_team"] = df["away_team_name"]
            df = df.reset_index(drop=True)
            self._baseline_columns = set(df.columns)
            _augment_dataframe(df, self.rolling_window)
            self._derived_columns = set(df.columns) - set(self._baseline_columns)
            self._df = df
            if "season" in df.columns:
                self._latest_season = (
                    df["season"]
                    .astype(int, errors="ignore")
                    .astype(str)
                    .max()
                )
            ensure_latest_team_caches(df)
        return self._df

    @property
    def latest_season(self) -> str:
        if self._latest_season is None:
            _ = self.df
        return self._latest_season or str(DEFAULT_DATASET_VERSION)

    @property
    def required_features(self) -> List[str]:
        if self._required_features is None:
            unique: Dict[str, None] = {}
            for feature in _flatten(self._model_features.values()):
                if feature not in unique:
                    unique[feature] = None
            self._required_features = list(unique.keys())
        return self._required_features

    @property
    def feature_lineage(self) -> Dict[str, FeatureOrigin]:
        lineage: Dict[str, FeatureOrigin] = {}
        baseline = self._baseline_columns or set()
        derived = self._derived_columns or set()
        for feature in self.required_features:
            if feature in baseline:
                lineage[feature] = FeatureOrigin.DIRECT
            elif feature in derived:
                lineage[feature] = FeatureOrigin.DERIVED
            else:
                lineage[feature] = FeatureOrigin.UNKNOWN
        return lineage

    def get_fixture_by_id(self, match_id: int) -> FixtureFeatures:
        row = self.df.loc[self.df["match_id"] == match_id]
        if row.empty:
            raise ValueError(f"match_id {match_id} not found in dataset")
        return self._build_features_from_row(row.iloc[0])

    def get_fixture(self, season: Optional[str], home: str, away: str) -> FixtureFeatures:
        season = season or self.latest_season
        df = self.df
        mask = (
            (df["season"].astype(str) == str(season))
            & (df["home_team_name"].str.lower() == home.lower())
            & (df["away_team_name"].str.lower() == away.lower())
        )
        row = df.loc[mask]
        if row.empty:
            raise ValueError(f"Fixture {home} vs {away} ({season}) not found")
        return self._build_features_from_row(row.iloc[0])

    def _build_features_from_row(self, row: pd.Series) -> FixtureFeatures:
        season = str(row["season"])
        home = str(row["home_team_name"])
        away = str(row["away_team_name"])
        cache_key = (_normalize_name(season), _normalize_name(home), _normalize_name(away))
        match_id = int(row["match_id"])
        if self.cache:
            cached = self.cache.get(
                self.dataset_version,
                cache_key[0],
                cache_key[1],
                cache_key[2],
                self.dataset_mtime,
            )
            if cached:
                feature_dict = {k: float(v) for k, v in cached.items()}
                return FixtureFeatures(
                    match_id=match_id,
                    home_team=home,
                    away_team=away,
                    season=season,
                    features=feature_dict,
                )
        features: Dict[str, float] = {}
        for feature in self.required_features:
            value = row.get(feature)
            if pd.isna(value):
                origin = self.feature_lineage.get(feature, FeatureOrigin.UNKNOWN)
                if origin is FeatureOrigin.UNKNOWN and feature not in self._unknown_features_logged:
                    LOGGER.warning(
                        "Feature '%s' missing from dataset %s; defaulting to 0.",
                        feature,
                        self.dataset_version,
                    )
                    self._unknown_features_logged.add(feature)
                features[feature] = 0.0
            else:
                features[feature] = float(value)
        if self.cache:
            self.cache.set(
                self.dataset_version,
                cache_key[0],
                cache_key[1],
                cache_key[2],
                self.dataset_mtime,
                match_id,
                features,
            )
        return FixtureFeatures(
            match_id=match_id,
            home_team=home,
            away_team=away,
            season=season,
            features=features,
        )


def _flatten(items: Iterable[Iterable[str]]) -> Iterable[str]:
    for seq in items:
        for value in seq:
            yield value


def _guess_version_from_name(filename: str) -> Optional[str]:
    for token in filename.split("_"):
        if token.isdigit():
            return token
    return None


def _augment_dataframe(df: pd.DataFrame, rolling_window: int) -> None:
    if "prob_edge" not in df.columns and {
        "forecast_home_win",
        "forecast_away_win",
    }.issubset(df.columns):
        df["prob_edge"] = (df["forecast_home_win"] - df["forecast_away_win"]).astype(np.float32).fillna(0.0)

    _prepare_smoothed_form(df, rolling_window)
    _prepare_shot_features(df, rolling_window)


def _prepare_smoothed_form(df: pd.DataFrame, rolling_window: int) -> None:
    window = rolling_window
    if "home_recent_games_frac" not in df.columns and {"season", "home_team_name"}.issubset(df.columns):
        if "match_datetime_utc" in df.columns:
            df.sort_values("match_datetime_utc", inplace=True)
        home_games = (
            df.groupby(["season", "home_team_name"], sort=False).cumcount().clip(upper=window).astype(float)
        )
        away_games = (
            df.groupby(["season", "away_team_name"], sort=False).cumcount().clip(upper=window).astype(float)
        )
        df["home_recent_games_frac"] = (home_games / window).astype(np.float32)
        df["away_recent_games_frac"] = (away_games / window).astype(np.float32)

    if "home_goals_for_avg5" not in df.columns and "home_goals_for_last_5" in df.columns:
        df["home_goals_for_avg5"] = _smoothed_avg(df["home_goals_for_last_5"], df["home_recent_games_frac"], window)
        df["home_goals_against_avg5"] = _smoothed_avg(df["home_goals_against_last_5"], df["home_recent_games_frac"], window)
        df["home_xg_for_avg5"] = _smoothed_avg(df["home_xg_for_last_5"], df["home_recent_games_frac"], window)
        df["home_xg_against_avg5"] = _smoothed_avg(df["home_xg_against_last_5"], df["home_recent_games_frac"], window)
        df["home_points_avg5"] = _smoothed_avg(df["home_points_last_5"], df["home_recent_games_frac"], window)

        df["away_goals_for_avg5"] = _smoothed_avg(df["away_goals_for_last_5"], df["away_recent_games_frac"], window)
        df["away_goals_against_avg5"] = _smoothed_avg(df["away_goals_against_last_5"], df["away_recent_games_frac"], window)
        df["away_xg_for_avg5"] = _smoothed_avg(df["away_xg_for_last_5"], df["away_recent_games_frac"], window)
        df["away_xg_against_avg5"] = _smoothed_avg(df["away_xg_against_last_5"], df["away_recent_games_frac"], window)
        df["away_points_avg5"] = _smoothed_avg(df["away_points_last_5"], df["away_recent_games_frac"], window)

    if "att_gap_avg5" not in df.columns and {"home_goals_for_avg5", "away_goals_for_avg5"}.issubset(df.columns):
        df["att_gap_avg5"] = df["home_goals_for_avg5"] - df["away_goals_for_avg5"]
        df["def_gap_avg5"] = df["away_goals_against_avg5"] - df["home_goals_against_avg5"]
        df["points_gap_avg5"] = df["home_points_avg5"] - df["away_points_avg5"]
        df["xg_att_gap_avg5"] = df["home_xg_for_avg5"] - df["away_xg_for_avg5"]
        df["xg_def_gap_avg5"] = df["away_xg_against_avg5"] - df["home_xg_against_avg5"]
        eps = 1e-3
        df["log_xg_ratio_avg5"] = np.log(
            (df["home_xg_for_avg5"] + eps) / (df["away_xg_for_avg5"] + eps)
        ).replace([np.inf, -np.inf], 0.0)


def _prepare_shot_features(df: pd.DataFrame, rolling_window: int) -> None:
    if not {"home_shots_for", "away_shots_for"}.issubset(df.columns):
        return
    for column in ("home_shots_for", "away_shots_for"):
        df[column] = pd.to_numeric(df[column], errors="coerce")
        median = df[column].median()
        df[column] = df[column].fillna(median if pd.notna(median) else 0.0)

    df["home_shots_allowed"] = df["away_shots_for"]
    df["away_shots_allowed"] = df["home_shots_for"]

    df["home_shots_for_avg5"] = _prior_rolling_mean(df, "home_team_name", "home_shots_for", rolling_window)
    df["away_shots_for_avg5"] = _prior_rolling_mean(df, "away_team_name", "away_shots_for", rolling_window)
    df["home_shots_allowed_avg5"] = _prior_rolling_mean(df, "home_team_name", "home_shots_allowed", rolling_window)
    df["away_shots_allowed_avg5"] = _prior_rolling_mean(df, "away_team_name", "away_shots_allowed", rolling_window)

    short_window = min(3, rolling_window)
    df["home_shots_for_avg3"] = _prior_rolling_mean(df, "home_team_name", "home_shots_for", short_window)
    df["away_shots_for_avg3"] = _prior_rolling_mean(df, "away_team_name", "away_shots_for", short_window)
    df["home_shots_allowed_avg3"] = _prior_rolling_mean(df, "home_team_name", "home_shots_allowed", short_window)
    df["away_shots_allowed_avg3"] = _prior_rolling_mean(df, "away_team_name", "away_shots_allowed", short_window)

    df["shot_vol_gap_avg5"] = df["home_shots_for_avg5"] - df["away_shots_for_avg5"]
    df["shot_suppress_gap_avg5"] = df["away_shots_allowed_avg5"] - df["home_shots_allowed_avg5"]
    eps = 1e-3
    df["log_shot_ratio_avg5"] = np.log(
        (df["home_shots_for_avg5"] + eps) / (df["away_shots_for_avg5"] + eps)
    ).replace([np.inf, -np.inf], 0.0)
    df["shots_tempo_avg5"] = (df["home_shots_for_avg5"] + df["away_shots_for_avg5"]) / 2.0

    df["shot_volume_gap_avg3"] = df["home_shots_for_avg3"] - df["away_shots_for_avg3"]
    df["shot_suppress_gap_avg3"] = df["away_shots_allowed_avg3"] - df["home_shots_allowed_avg3"]
    df["shots_tempo_avg3"] = (df["home_shots_for_avg3"] + df["away_shots_for_avg3"]) / 2.0

    df["shot_volume_gap_avg3_season_z"] = _season_zscore(df, "shot_volume_gap_avg3")
    df["shot_suppress_gap_avg3_season_z"] = _season_zscore(df, "shot_suppress_gap_avg3")
    df["shots_tempo_avg3_season_z"] = _season_zscore(df, "shots_tempo_avg3")

    for column in [
        "home_shots_for_avg5",
        "away_shots_for_avg5",
        "home_shots_allowed_avg5",
        "away_shots_allowed_avg5",
        "home_shots_for_avg3",
        "away_shots_for_avg3",
        "home_shots_allowed_avg3",
        "away_shots_allowed_avg3",
        "shot_vol_gap_avg5",
        "shot_suppress_gap_avg5",
        "shot_volume_gap_avg3",
        "shot_suppress_gap_avg3",
        "shots_tempo_avg5",
        "shots_tempo_avg3",
    ]:
        df[column] = df[column].astype(np.float32).fillna(0.0)


def _prior_rolling_mean(df: pd.DataFrame, team_col: str, value_col: str, window: int) -> pd.Series:
    series = (
        df.groupby(team_col, sort=False)[value_col]
        .transform(lambda s: s.rolling(window, min_periods=1).mean().shift(1))
    )
    fallback = (
        df.groupby(team_col, sort=False)[value_col]
        .transform(lambda s: s.shift(1))
        .fillna(df[value_col].median(skipna=True))
    )
    return series.fillna(fallback).fillna(0.0).astype(np.float32)


def _season_zscore(df: pd.DataFrame, column: str) -> pd.Series:
    grouped = df.groupby("season")[column]
    mean = grouped.transform("mean")
    std = grouped.transform("std").replace(0.0, np.nan)
    z = (df[column] - mean) / std
    return z.replace([np.inf, -np.inf], 0.0).fillna(0.0).astype(np.float32)


def _smoothed_avg(sum_series: pd.Series, games_frac: pd.Series, window: int) -> pd.Series:
    games = games_frac * window
    per_match = sum_series / games.replace(0.0, np.nan)
    prior = per_match.dropna().mean()
    prior = 0.0 if np.isnan(prior) else prior
    per_match = per_match.fillna(prior)
    alpha = games_frac.clip(0.0, 1.0)
    return (alpha * per_match + (1.0 - alpha) * prior).astype(np.float32)


def export_fixture_features(match_id: int, output: Path, store: Optional[FeatureStore] = None) -> None:
    store = store or FeatureStore()
    fixture = store.get_fixture_by_id(match_id)
    output.write_text(json.dumps(fixture.features, indent=2), encoding="utf-8")


if __name__ == "__main__":  # pragma: no cover
    import argparse

    parser = argparse.ArgumentParser(description="Fixture feature extractor")
    parser.add_argument("match_id", type=int)
    parser.add_argument("--output", type=Path, default=Path("fixture_features.json"))
    parser.add_argument(
        "--dataset-version",
        dest="dataset_version",
        help="Dataset version label, e.g., 7",
    )
    parser.add_argument(
        "--dataset",
        dest="dataset_path",
        type=Path,
        help="Explicit dataset CSV path",
    )
    args = parser.parse_args()
    store_kwargs = {}
    if args.dataset_version:
        store_kwargs["dataset_version"] = args.dataset_version
    if args.dataset_path:
        store_kwargs["dataset_path"] = args.dataset_path
    store = FeatureStore(**store_kwargs)
    export_fixture_features(args.match_id, args.output, store=store)
    print(f"Wrote features to {args.output}")
