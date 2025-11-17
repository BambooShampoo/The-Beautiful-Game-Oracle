"""Utility helpers for caching team rosters per league/season.

The cache lets the web layer resolve future fixtures even when the exact
matchup hasn't occurred yet by reusing the most recent roster metadata.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Iterable, List, Sequence

import pandas as pd

TEAM_CACHE_DIR = Path("understat_data") / "team_cache"


def slugify(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", name.strip().lower()).strip("_")


def short_name(name: str) -> str:
    clean = re.sub(r"[^A-Za-z ]+", "", name).strip()
    if not clean:
        return name[:3].upper()
    parts = clean.split()
    if len(parts) == 1:
        return parts[0][:3].upper()
    return "".join(part[0].upper() for part in parts[:3])


def _team_cache_path(league: str, season: str) -> Path:
    safe_league = slugify(league).upper()
    return TEAM_CACHE_DIR / f"{safe_league}_{season}.json"


def ensure_team_cache(df: pd.DataFrame, league: str, season: str) -> Path:
    """Persist the roster for (league, season) if it isn't cached yet."""

    TEAM_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_path = _team_cache_path(league, season)
    if cache_path.exists():
        return cache_path

    mask = (df["league"].astype(str) == str(league)) & (
        df["season"].astype(str) == str(season)
    )
    subset = df.loc[mask]
    if subset.empty:
        raise ValueError(f"No fixtures found for league={league} season={season}")

    team_names: List[str] = sorted(
        set(subset["home_team_name"].astype(str)) | set(subset["away_team_name"].astype(str))
    )
    payload = {
        "league": str(league),
        "season": str(season),
        "teams": [
            {
                "name": name,
                "canonical": slugify(name),
                "shortName": short_name(name),
            }
            for name in team_names
        ],
    }
    cache_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return cache_path


def ensure_latest_team_caches(df: pd.DataFrame) -> Sequence[Path]:
    """Ensure every league has a cache for its latest season present in df."""

    produced: List[Path] = []
    if "league" not in df.columns or "season" not in df.columns:
        return produced
    latest_by_league = (
        df.assign(season=df["season"].astype(str))
        .groupby("league")["season"]
        .max()
    )
    for league, season in latest_by_league.items():
        try:
            produced.append(ensure_team_cache(df, league, season))
        except ValueError:
            continue
    return produced
