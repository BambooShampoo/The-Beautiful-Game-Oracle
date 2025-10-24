import ast
import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

INPUT_PATH = Path("understat_data") / "league_results.csv"
OUTPUT_PATH = Path("understat_data") / "league_results_cleaned.csv"


def parse_nested(value: Any) -> Dict[str, Any]:
    """Parse serialized dict-like strings into dictionaries."""
    if value is None or value == "":
        return {}

    if isinstance(value, dict):
        return value

    if isinstance(value, str):
        value = value.strip()
        if not value:
            return {}

        try:
            return ast.literal_eval(value)
        except (ValueError, SyntaxError):
            try:
                return json.loads(value.replace("'", '"'))
            except (json.JSONDecodeError, TypeError):
                return {}
    return {}


def compute_outcome(home_goals: int, away_goals: int) -> str:
    if home_goals > away_goals:
        return "Home Win"
    if home_goals < away_goals:
        return "Away Win"
    return "Draw"


def process_league_results():
    if not INPUT_PATH.exists():
        raise FileNotFoundError(f"Input file not found: {INPUT_PATH}")

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "match_id",
        "league",
        "season",
        "match_datetime_utc",
        "match_date",
        "match_time",
        "is_result",
        "home_team_id",
        "home_team_name",
        "home_team_short",
        "away_team_id",
        "away_team_name",
        "away_team_short",
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
        "match_outcome",
        "match_outcome_code",
        "home_win_flag",
        "draw_flag",
        "away_win_flag",
    ]

    with INPUT_PATH.open(newline="") as infile, OUTPUT_PATH.open(
        "w", newline=""
    ) as outfile:
        reader = csv.DictReader(infile)
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()

        for row in reader:
            home_meta = parse_nested(row.get("h"))
            away_meta = parse_nested(row.get("a"))
            goals_meta = parse_nested(row.get("goals"))
            xg_meta = parse_nested(row.get("xG"))
            forecast_meta = parse_nested(row.get("forecast"))

            match_dt_raw = row.get("datetime", "")
            try:
                match_dt = datetime.fromisoformat(match_dt_raw.strip())
            except ValueError:
                match_dt = None

            home_goals = int(goals_meta.get("h", 0)) if goals_meta else 0
            away_goals = int(goals_meta.get("a", 0)) if goals_meta else 0
            home_xg = float(xg_meta.get("h", 0.0)) if xg_meta else 0.0
            away_xg = float(xg_meta.get("a", 0.0)) if xg_meta else 0.0

            outcome = compute_outcome(home_goals, away_goals)
            outcome_code = {"Home Win": "H", "Draw": "D", "Away Win": "A"}[outcome]

            writer.writerow(
                {
                    "match_id": int(row.get("id", 0)),
                    "league": row.get("League", ""),
                    "season": int(row.get("Season", 0))
                    if row.get("Season")
                    else "",
                    "match_datetime_utc": match_dt.isoformat(sep=" ")
                    if match_dt
                    else match_dt_raw,
                    "match_date": match_dt.date().isoformat()
                    if match_dt
                    else "",
                    "match_time": match_dt.time().isoformat()
                    if match_dt
                    else "",
                    "is_result": row.get("isResult", "").strip().lower() == "true",
                    "home_team_id": int(home_meta.get("id", 0))
                    if home_meta
                    else "",
                    "home_team_name": home_meta.get("title", "")
                    if home_meta
                    else "",
                    "home_team_short": home_meta.get("short_title", "")
                    if home_meta
                    else "",
                    "away_team_id": int(away_meta.get("id", 0))
                    if away_meta
                    else "",
                    "away_team_name": away_meta.get("title", "")
                    if away_meta
                    else "",
                    "away_team_short": away_meta.get("short_title", "")
                    if away_meta
                    else "",
                    "home_goals": home_goals,
                    "away_goals": away_goals,
                    "total_goals": home_goals + away_goals,
                    "goal_difference": home_goals - away_goals,
                    "home_xg": round(home_xg, 6),
                    "away_xg": round(away_xg, 6),
                    "xg_difference": round(home_xg - away_xg, 6),
                    "forecast_home_win": float(forecast_meta.get("w", 0.0))
                    if forecast_meta
                    else 0.0,
                    "forecast_draw": float(forecast_meta.get("d", 0.0))
                    if forecast_meta
                    else 0.0,
                    "forecast_away_win": float(forecast_meta.get("l", 0.0))
                    if forecast_meta
                    else 0.0,
                    "match_outcome": outcome,
                    "match_outcome_code": outcome_code,
                    "home_win_flag": 1 if outcome_code == "H" else 0,
                    "draw_flag": 1 if outcome_code == "D" else 0,
                    "away_win_flag": 1 if outcome_code == "A" else 0,
                }
            )


if __name__ == "__main__":
    process_league_results()
