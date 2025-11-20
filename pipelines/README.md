# Pipelines Toolkit

Utilities for exporting trained notebook models and reproducing feature engineering locally.

## Feature Store

- `feature_store.py` loads `understat_data/Dataset_Version_7.csv` and rebuilds the performance/financial/market feature sets used in the notebook.
- `FeatureStore.get_fixture(...)` returns `FixtureFeatures` with aligned feature vectors for inference.
- Future work: add caching (Parquet/SQLite) and parity tests against the notebook outputs.

## Export Helpers

- `export_artifacts.py` exposes functions to convert TensorFlow/Keras models to TFJS/ONNX and to serialize preprocessing bundles.
- `export_cli.py` demonstrates how notebook cells will call the exporters (currently stubbed with a dummy model so the wiring can be tested outside Kaggle).

Run `PYTHONPATH=. python -m pipelines.export_cli --output-dir artifacts/dev_models/performance` to generate placeholder artefacts while wiring the inference stack. Replace the dummy exporter with calls to the actual models in `Football Predictor Models.ipynb` once training notebooks produce final checkpoints.
