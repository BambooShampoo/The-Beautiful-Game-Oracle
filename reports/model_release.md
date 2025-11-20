# Model Release Workflow

This pipeline publishes every retraining run to a versioned manifest so the Vercel frontend can hot‑swap models safely.

## Artefact Checklist

1. **Trained models:** export each baseline (`performance_dense`, `financial_dense`, `market_odds`) as TensorFlow.js, ONNX, or another deployment-friendly format. Artefacts can live locally or inside a Kaggle dataset—the manifest will embed both references.
2. **Preprocessing assets:** scaler statistics, feature order lists, categorical encoders.
3. **Attribution caches:** precomputed SHAP / LOO matrices per signal family so the UI can serve explanations instantly.
4. **Metrics:** log-loss, calibration, confusion matrices, or other evaluation metadata to embed in the manifest.

Store these files under a staging directory (e.g., `export/latest_run/`) prior to publishing.

## Publishing Instructions

1. Activate the repo virtualenv and install dev tools: `pip install -r requirements-dev.txt`.
2. Run a dry-run manifest build to verify inputs (example below shows Kaggle URLs; omit `--artefact-base-url` to rely entirely on local paths for development):

   ```bash
   python scripts/publish_model.py \
     --run-id 2024-05-20-v7 \
     --dataset-version 7 \
     --model performance_dense=export/latest_run/performance/model.json:tfjs \
     --model financial_dense=export/latest_run/financial/model.onnx:onnx \
     --model market_odds=export/latest_run/market/model.json:tfjs \
     --preprocessing scalers=export/latest_run/preprocessing/scalers.json \
     --attribution performance_shap=export/latest_run/attrib/perf_shap.npz \
     --attribution financial_shap=export/latest_run/attrib/fin_shap.npz \
     --metrics-file export/latest_run/metrics.json \
     --artefact-base-url https://www.kaggleusercontent.com/datasets/<id>/<run> \
     --dry-run
   ```

3. When validation passes, rerun without `--dry-run` to write `artifacts/manifests/<run_id>.json`.
4. Upload the artefact bundle + manifest to the Kaggle dataset (or chosen storage) and increment the experiment registry CSV with run metadata.
5. Trigger the Vercel `/api/reload` hook (when available) to refresh servers without redeploying. For local-only testing, point the loader at the newly written manifest under `artifacts/manifests/`. You can automate steps 2–5 with `scripts/publish_and_refresh.sh` which wraps `publish_model.py` and then calls the reload endpoint via `scripts/trigger_frontend_refresh.py`.

## Testing

- `python -m pytest tests/test_manifest_schema.py tests/test_publish_model.py` ensures both the schema and publisher logic behave as expected.
- The script validates manifests with `jsonschema`, so malformed entries (missing SHA, invalid timestamps) fail fast before uploading.

Keep each manifest under source control so every deployment references an immutable, audited configuration.
- `scripts/trigger_frontend_refresh.py --endpoint <reload_url> --token <secret>` calls the `/api/reload` route so new manifests hydrate the Vercel runtime without a full deploy.
- `scripts/publish_and_refresh.sh` orchestrates manifest creation and reload triggering in one command; integrate this script into CI once Kaggle runs finish exporting artefacts.
