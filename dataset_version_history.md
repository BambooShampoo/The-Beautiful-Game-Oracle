# Dataset Version History

This document captures every data-centric change that accompanied commits referencing “Kaggle Notebook | Football Predictor Model.ipynb | …”. It focuses on the dataset builders, helper utilities, and CSV artefacts that shaped model behaviour across the project.

## Cleaned Understat Export Foundation
- `cleanLeagueResults.py` parses the raw Understat dumps, normalises nested JSON strings, and writes `understat_data/league_results_cleaned.csv` with consistent datetime fields, goal/xG statistics, bookmaker forecasts, and one-hot outcome flags.  
- This cleaned export is the source for all downstream feature engineering, keeping season/league values stable for TensorFlow ingestion.

## Dataset_Version_2 – tf.data-Aligned Base Table
- `analysis/build_league_results_v2.py` enriches the cleaned league results with rolling five-match aggregates, calendar intensity markers, market-derived diagnostics, and per-season momentum z-scores. The script emits both `understat_data/league_results_v2.csv` and the canonical `understat_data/Dataset.csv`.
- Companion utilities introduced in the same iteration:
  - `analysis/dataset_vnext_scoping.py` for coverage checks, calibration plots, and quick logistic baselines that guide feature tweaks.
  - `analysis/split_dataset_v2_features.py` which saves the model-specific feature views (performance, momentum, market) consumed by the Kaggle notebook.
  - `analysis/sync_run_history.py` to keep Kaggle experiment logs aligned with dataset labels in `baseline_run_history.csv`.

## Dataset_Version_3 – Shots & Elo Expectations
- `build_dataset_version3.py` appends shot counts from `Team_Results/team_results.csv` and pre-match Elo metrics reconstructed from `team_elos_timeseries.csv` to the v2 base table, producing `understat_data/Dataset_Version_3.csv`.
- Columns added: `home_shots_for`, `away_shots_for`, `elo_home_pre`, `elo_away_pre`, and `elo_home_expectation`, enabling models to weigh shot momentum and team-strength priors simultaneously.

## Dataset_Version_4 – Full Elo Profiles
- `build_dataset_version4.py` keeps the v3 features and joins per-team summary standings from `team_elos_v2.csv` (final Elo, played, wins/draws/losses, points pct). The script still sources shots + Elo per match but now records summary metrics so notebooks can inject league-table context.
- Output artefact: `understat_data/Dataset_Version_4.csv` (coverage through 2024 seasons).

## Dataset_Version_5 – Market vs Elo Harmonisation
- Commit `6e8d0c0` rewrote the builder to rebuild the base table directly from `understat_data/EPL/<season>/league_results.csv`, ensuring new seasons propagate without manual merges.  
- `build_dataset_version5.py`:
  - Recomputes pre-match Elo ratings, expectations, and per-season gap z-scores.
  - Adds `elo_mean_pre`, `elo_gap_pre`, `elo_expectation_gap`, and their season-standardised variants.
  - Writes a clipped `market_vs_elo_edge` column (±0.35) capturing bookmaker deviations from Elo.  
- `Dataset_Version_5_changes.md` documents the SHAP/LOO motivation (market drift, redundant temporal dummies) that triggered the update. The CSV (`understat_data/Dataset_Version_5.csv`) contains 1,140 EPL matches (2022‑2024).

## Dataset_Version_6 – Season Window Adjustments
- Commit `9708db1` reused the Version 5 builder but regenerated the dataset after ingesting early 2025 fixtures.  
- `understat_data/Dataset_Version_6.csv` now covers 2022‑2025 (110 matches through 9 Nov 2025), allowing the Kaggle notebook to drop 2022/2023 for stress tests while holding out fall 2025 as the evaluation split without changing the builder logic.

## Dataset_Version_7 – Volatility & Momentum Differentials
- Commits `5762c49` and `a00ecbb` cloned the V5 builder into `build_dataset_version7.py` and layered volatility diagnostics:
  - Rolling standard deviation features for goal/xG/shot differential (`home_goal_diff_std5`, `xg_diff_std_gap5`, etc.).
  - Exponential moving averages (α = 0.55) for the same signals plus home-away gap columns.
  - Chronological sorting + a two-phase volatility update to avoid post-match leakage (first read current buffers, then append each result).
- The change log (`Dataset_Version_7_changes.md`) and `Performance_Model_Features.md` were updated to describe the new features and warn that `market_vs_elo_edge` is excluded from the performance view to prevent odds leakage.
- `understat_data/Dataset_Version_7.csv` mirrors the V6 season coverage but bakes in volatility signals for SHAP and LOO analysis.

---

Keep this file updated whenever a new dataset iteration (or diagnostic script) lands so downstream TensorFlow/Keras pipelines and Kaggle submissions stay reproducible.
