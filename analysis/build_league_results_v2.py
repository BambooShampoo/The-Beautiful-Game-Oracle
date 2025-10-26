#!/usr/bin/env python3
"""
Build EPL league results dataset (version 2) with engineered features.

Uses the cleaned Understat export (version 1) and adds pre-match form,
rest, and market-derived diagnostics suited for downstream modelling and
attribution analysis.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Iterable, List

import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parent.parent
INPUT_PATH = PROJECT_ROOT / "understat_data" / "league_results_cleaned.csv"
OUTPUT_PATH = PROJECT_ROOT / "understat_data" / "league_results_v2.csv"


def load_v1() -> pd.DataFrame:
    """Load version 1 dataset with consistent dtypes."""
    df = pd.read_csv(INPUT_PATH)
    df["is_result"] = df["is_result"].astype(bool)
    df = df[df["is_result"]].copy()
    df = df[df["league"] == "EPL"].copy()
    df["match_datetime_utc"] = pd.to_datetime(df["match_datetime_utc"])
    df["match_date"] = pd.to_datetime(df["match_date"])
    numeric_cols = [
        "home_goals",
        "away_goals",
        "total_goals",
        "goal_difference",
        "home_xg",
        "away_xg",
        "xg_difference",
        "forecast_home_win",
        "forecast_draw",
        "forecast_away_win",
    ]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df["season"] = df["season"].astype(int)
    df = df[df["season"] <= 2024].copy()
    df["match_weekday"] = df["match_date"].dt.day_name()
    df = df.drop(columns=["match_time", "home_team_short", "away_team_short"], errors="ignore")
    return df.sort_values("match_datetime_utc").reset_index(drop=True)


def compute_team_view(matches: pd.DataFrame) -> pd.DataFrame:
    """Transform match table into a long team-centric view with shifts."""

    def outcome_points(code: str) -> tuple[int, int]:
        if code == "H":
            return 3, 0
        if code == "A":
            return 0, 3
        return 1, 1

    home_pts, away_pts = zip(*matches["match_outcome_code"].map(outcome_points))
    matches = matches.assign(home_points=home_pts, away_points=away_pts)

    home_cols = {
        "home_team_id": "team_id",
        "home_team_name": "team_name",
        "home_points": "points",
        "home_goals": "goals_for",
        "away_goals": "goals_against",
        "home_xg": "xg_for",
        "away_xg": "xg_against",
    }
    away_cols = {
        "away_team_id": "team_id",
        "away_team_name": "team_name",
        "away_points": "points",
        "away_goals": "goals_for",
        "home_goals": "goals_against",
        "away_xg": "xg_for",
        "home_xg": "xg_against",
    }

    home_df = matches[["match_id", "match_datetime_utc", "season", *home_cols.keys()]].rename(columns=home_cols)
    home_df["is_home"] = 1

    away_df = matches[["match_id", "match_datetime_utc", "season", *away_cols.keys()]].rename(columns=away_cols)
    away_df["is_home"] = 0

    long_df = pd.concat([home_df, away_df], ignore_index=True).sort_values(
        ["team_id", "match_datetime_utc"]
    )
    long_df["goal_diff"] = long_df["goals_for"] - long_df["goals_against"]
    long_df["xg_diff"] = long_df["xg_for"] - long_df["xg_against"]
    long_df["match_number"] = long_df.groupby("team_id").cumcount()

    long_df["rest_days"] = (
        long_df.groupby("team_id")["match_datetime_utc"]
        .diff()
        .dt.total_seconds()
        .div(86400)
    )
    return long_df.reset_index(drop=True)


def add_rolling_features(long_df: pd.DataFrame) -> pd.DataFrame:
    """Attach pre-match rolling aggregates for performance signals."""
    feature_specs: Dict[str, str] = {
        "points": "sum",
        "goals_for": "sum",
        "goals_against": "sum",
        "goal_diff": "sum",
        "xg_for": "sum",
        "xg_against": "sum",
        "xg_diff": "sum",
    }
    windows = (3, 5, 10)
    grouped = long_df.groupby("team_id", group_keys=False)

    for col, agg in feature_specs.items():
        for window in windows:
            new_col = f"{col}_last_{window}"
            long_df[new_col] = grouped[col].transform(
                lambda s, w=window: s.shift().rolling(window=w, min_periods=1).sum()
            )

    long_df["rest_days_prev"] = grouped["rest_days"].transform(lambda s: s.shift())
    long_df["rest_days_prev"] = long_df["rest_days_prev"].fillna(0)
    long_df["rest_days_capped"] = long_df["rest_days_prev"].clip(upper=28.0)
    long_df["rest_reset_flag"] = (long_df["rest_days_prev"] > 35).astype(int)

    for window in windows:
        denom = 3 * long_df["match_number"].clip(upper=window)
        denom = denom.replace(0, np.nan)
        long_df[f"points_pct_last_{window}"] = long_df[f"points_last_{window}"] / denom

    long_df.fillna(0, inplace=True)
    return long_df


def pivot_features(matches: pd.DataFrame, long_df: pd.DataFrame) -> pd.DataFrame:
    """Join team aggregates back to matches with home/away prefixes."""
    base_feature_cols = [
        "match_id",
        "match_number",
        "rest_days_prev",
        "rest_days_capped",
        "rest_reset_flag",
    ]
    rolling_cols = [
        col
        for col in long_df.columns
        if col.endswith(("last_3", "last_5", "last_10"))
        or col.startswith("points_pct_last_")
    ]
    feature_cols = base_feature_cols + rolling_cols

    home_features = (
        long_df[long_df["is_home"] == 1][feature_cols]
        .set_index("match_id")
        .add_prefix("home_")
    )
    away_features = (
        long_df[long_df["is_home"] == 0][feature_cols]
        .set_index("match_id")
        .add_prefix("away_")
    )

    enriched = (
        matches.set_index("match_id")
        .join(home_features, how="left")
        .join(away_features, how="left")
        .reset_index()
    )

    enriched["home_matches_played"] = enriched["home_match_number"]
    enriched["away_matches_played"] = enriched["away_match_number"]

    enriched["form_diff_last5"] = (
        enriched["home_points_last_5"] - enriched["away_points_last_5"]
    )
    enriched["form_pct_diff_last5"] = (
        enriched["home_points_pct_last_5"] - enriched["away_points_pct_last_5"]
    )
    enriched["xg_diff_last5"] = (
        enriched["home_xg_diff_last_5"] - enriched["away_xg_diff_last_5"]
    )
    enriched["rest_diff"] = (
        enriched["home_rest_days_capped"] - enriched["away_rest_days_capped"]
    )
    enriched["rest_reset_flag_pair"] = (
        enriched["home_rest_reset_flag"] | enriched["away_rest_reset_flag"]
    )
    enriched["season_phase_home"] = (
        enriched["home_matches_played"] / 38.0
    ).clip(upper=1)
    enriched["season_phase_away"] = (
        enriched["away_matches_played"] / 38.0
    ).clip(upper=1)
    return enriched


def add_market_features(df: pd.DataFrame) -> pd.DataFrame:
    """Engineer market-signal derived features."""
    epsilon = 1e-6
    for col in ["forecast_home_win", "forecast_draw", "forecast_away_win"]:
        df[col] = df[col].clip(epsilon, 1 - epsilon)

    total = df["forecast_home_win"] + df["forecast_draw"] + df["forecast_away_win"]
    df["forecast_home_win"] /= total
    df["forecast_draw"] /= total
    df["forecast_away_win"] /= total

    df["market_home_edge"] = df["forecast_home_win"] - df["forecast_away_win"]
    df["market_expected_points_home"] = (
        3 * df["forecast_home_win"] + df["forecast_draw"]
    )
    df["market_expected_points_away"] = (
        3 * df["forecast_away_win"] + df["forecast_draw"]
    )

    def entropy(row: pd.Series) -> float:
        probs = row[["forecast_home_win", "forecast_draw", "forecast_away_win"]].astype(float).values
        return float(-(probs * np.log(probs)).sum())

    df["market_entropy"] = df.apply(entropy, axis=1)
    df["market_logit_home"] = np.log(
        df["forecast_home_win"] / df["forecast_away_win"]
    )
    df["market_max_prob"] = df[
        ["forecast_home_win", "forecast_draw", "forecast_away_win"]
    ].max(axis=1)
    return df


def add_targets(df: pd.DataFrame) -> pd.DataFrame:
    """Create modelling-friendly target encodings."""
    mapping = {"H": 2, "D": 1, "A": 0}
    df["outcome_label"] = df["match_outcome_code"]
    df["outcome_id"] = df["match_outcome_code"].map(mapping).astype(int)
    df["home_points_actual"] = df["home_win_flag"] * 3 + df["draw_flag"] * 1
    df["away_points_actual"] = df["away_win_flag"] * 3 + df["draw_flag"] * 1
    return df


def reorder_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Reorder columns into core metadata, targets, market, and performance."""
    base_cols = [
        "match_id",
        "league",
        "season",
        "match_datetime_utc",
        "match_date",
        "match_weekday",
        "home_team_id",
        "home_team_name",
        "away_team_id",
        "away_team_name",
    ]
    result_cols = [
        "home_goals",
        "away_goals",
        "total_goals",
        "goal_difference",
        "home_xg",
        "away_xg",
        "xg_difference",
        "match_outcome",
        "match_outcome_code",
        "outcome_label",
        "outcome_id",
        "home_win_flag",
        "draw_flag",
        "away_win_flag",
        "home_points_actual",
        "away_points_actual",
    ]
    market_cols = [
        "forecast_home_win",
        "forecast_draw",
        "forecast_away_win",
        "market_home_edge",
        "market_expected_points_home",
        "market_expected_points_away",
        "market_entropy",
        "market_logit_home",
        "market_max_prob",
    ]
    perf_cols = sorted(
        [
            col
            for col in df.columns
            if col.startswith(("home_", "away_", "form_", "xg_", "season_phase", "rest_"))
            and col not in base_cols
            and col not in result_cols
        ]
    )
    remaining = [col for col in df.columns if col not in base_cols + result_cols + market_cols + perf_cols]
    ordered = base_cols + result_cols + market_cols + perf_cols + remaining
    return df[ordered]


def main() -> None:
    matches_v1 = load_v1()
    long_df = compute_team_view(matches_v1)
    long_df = add_rolling_features(long_df)
    enriched = pivot_features(matches_v1, long_df)
    enriched = add_market_features(enriched)
    enriched = add_targets(enriched)
    enriched = reorder_columns(enriched)
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    enriched.to_csv(OUTPUT_PATH, index=False)
    print(f"Saved version 2 dataset with {len(enriched)} rows to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
