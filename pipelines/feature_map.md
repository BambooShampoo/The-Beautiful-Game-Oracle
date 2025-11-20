# Feature Map – Notebook Parity

This registry documents how the API/local feature stores recover the 45-ish inputs consumed by each notebook model family. Mappings are auto-discovered from the latest `artifacts/experiments/run_*/<model>/metrics.json`, and `pipelines/feature_store.FeatureStore` consolidates them before serving Python/ONNX inference.

| Feature Family | Model(s) | Source |
| --- | --- | --- |
| Performance momentum + volatility | `performance_dense` | Direct columns for volatility (`*_std5`, `*_exp_decay`) already live inside `Dataset_Version_X.csv`. Rolling form stats (`home_recent_games_frac`, `*_avg5`, `log_xg_ratio_avg5`) are re-derived from the `_last_5` aggregates exactly as in `Football Predictor Models.ipynb` using `_smoothed_avg`. |
| Shot volume & suppression | `performance_dense`, `momentum_policy_rl` | Derived via `_prior_rolling_mean` on `home_shots_for`, `away_shots_for` with 5- and 3-match windows. Season-normalised versions (`shot_volume_gap_avg3_season_z`, etc.) are recovered via `_season_zscore`. |
| Market + Elo alignment | `market_gradient_boost`, `momentum_policy_rl` | Direct columns include bookmaker probabilities, entropy, Elo ratings, and `market_vs_elo_edge`. The inferred `prob_edge = forecast_home_win - forecast_away_win` mirrors the notebook’s `prob_edge` helper. |
| Momentum / congestion diagnostics | `momentum_policy_rl` | Already materialised inside the dataset builders; FeatureStore simply exposes them and logs if a column is absent. |
| Calendar controls | `market_gradient_boost`, `momentum_policy_rl` | `match_day_index`, `match_day_of_year_norm`, and weekday indexes originate from dataset exports; no additional processing is required. |

## Dataset Awareness

- FeatureStore detects the freshest run under `artifacts/experiments` and reads each model’s `feature_cols` list to decide which columns to emit. If no notebook metadata is present, it falls back to the static lists in this document (mirroring the notebook).
- The resolved dataset version follows this priority: CLI/env override (`FEATURE_DATASET_VERSION`) → dataset label recorded in the latest run metrics → default `Dataset_Version_7.csv`.

## Caching + Provenance

- Every computed feature vector is cached to `understat_data/feature_cache.sqlite`, keyed by `(dataset_version, season, home, away)` and invalidated whenever the dataset mtime changes.
- `FeatureStore.feature_lineage` flags whether each feature was a direct column, derived column, or still missing (`UNKNOWN`). Unknowns are logged so engineering work can prioritise true gaps instead of silent zero-fill.

## Notebook References

- Rolling form helpers (`_smoothed_avg`, `_prior_rolling_mean`) and season z-scores match the definitions in `Football Predictor Models.ipynb` (see the exported `football_predictor_models.py` for the exact code path).
- When adding new columns to the dataset builders, update the notebook, re-export metrics, and FeatureStore will automatically pick up the revised schema on the next run.
