"""CLI for running local predictions using exported models."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from pipelines.feature_store import FeatureStore


def main():
    parser = argparse.ArgumentParser(description="Predict fixture outcome locally")
    parser.add_argument("season", nargs="?", help="Season identifier, e.g., 2025")
    parser.add_argument("home", help="Home team name")
    parser.add_argument("away", help="Away team name")
    parser.add_argument("--output", type=Path)
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
    fixture = store.get_fixture(args.season, args.home, args.away)
    payload = {
        "match_id": fixture.match_id,
        "home": fixture.home_team,
        "away": fixture.away_team,
        "season": fixture.season,
        "features": fixture.features,
    }
    text = json.dumps(payload, indent=2)
    if args.output:
        args.output.write_text(text, encoding="utf-8")
        print(f"Wrote features to {args.output}")
    else:
        print(text)


if __name__ == "__main__":  # pragma: no cover
    main()
