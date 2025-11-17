# Vercel Front-End Commit Plan

This roadmap captures the full implementation scope for the EPL prediction portal so every retraining cycle automatically updates the Vercel site. Each numbered section maps to a single commit with clear architecture decisions, file touches, and validation notes.

## Commit 1 – Scaffold Web Workspace & Shared Config
- Add `web/` directory with Next.js 14 (App Router) + TypeScript + Tailwind setup via `create-next-app`.
- Establish base layouts (dark-friendly palette, reusable card components) and lint/prettier configs that match repo standards.
- Introduce `.env.example` describing `MODEL_MANIFEST_URL`, `KAGGLE_DATASET_ID`, `VERCEL_ANALYTICS_TOKEN`.
- Tests: `npm run lint`, `npm run build`, and a Playwright smoke test for home layout rendering (to be defined once e2e harness is added).

## Commit 2 – Model Manifest Contract & Publisher Script
- Define `artifacts/manifest_schema.json` describing `run_id`, dataset version, scaler hashes, SHAP cache URIs, checksums, and both remote + local availability metadata.
- Implement `scripts/publish_model.py` to package notebook exports (`tfjs`/`onnx`, preprocessing JSON, SHAP arrays) and emit a signed `model_manifest.json`. Script uploads payloads to Kaggle Dataset API (or local `artifacts/<run_id>/`) and updates experiment registry CSV. Support dual references so manifests can be consumed from Kaggle or directly from a developer’s filesystem.
- Document workflow in `reports/model_release.md`, outlining both Kaggle-hosted and local-only deployments.
- Tests: `python -m pytest tests/test_manifest_schema.py` (schema validation), integration dry-run for publisher using temporary directories, CLI invocation coverage via `python scripts/publish_model.py --dry-run`.

## Commit 3 – API Loader & Hot-Swap Plumbing
- Inside `web/src/server/models/`, create loader that fetches manifest URL on cold start, caches active models in memory, and exposes `reloadModels()` to refresh weights without redeploying. Loader should detect whether artefacts should be read from remote URLs or local filesystem paths provided in the manifest so local training exports can serve the site without Kaggle.
- Support tfjs graph-model loads plus preprocessing transforms (feature ordering, scaling, alias mapping). Keep last-good snapshot for rollback.
- Implement `/api/status` and `/api/reload` routes; the latter requires `RELOAD_TOKEN`.
- Tests: Vitest/Jest unit coverage for loader, supertest-based API tests for `/api/status` and `/api/reload`, plus mocked network failure scenarios.

## Commit 4 – Prediction Endpoint & Feature Stitching
- Build `/api/predict` route that validates team inputs, constructs feature vectors by pulling latest aggregates from precomputed JSONs (`latest_form.json`, `team_metadata.json`), and runs inference across performance/financial/market models whether they were produced on Kaggle or from local training sessions (use loader-supplied locations).
- Ensemble method: logit-average + optional weight overrides per manifest metadata.
- Response payload includes per-model logits, class probabilities, preprocessing hash, and reference to attribution indices (SHAP row ID, LOO group deltas).
- Tests: supertest integration against canned fixtures, golden-file comparison with notebook logits, and adversarial validation for missing inputs / invalid team combos.

## Commit 5 – Front-End UX (Selector, Results, Context)
- Implement hero + explainer sections summarizing project goals, dataset version, and currently active `run_id`, indicating whether predictions stem from Kaggle-hosted artefacts or locally mounted training runs.
- Build dual team selectors with search & crest previews (Combobox component) limited to EPL metadata. Source the options from the dataset (e.g., `Dataset_Version_7.csv`) so every club appears automatically when new seasons are added, falling back to local JSON only when the dataset isn't available yet. A dedicated `usePredict` hook should call `/api/predict`, surface loading/error states, cache the most recent successful request, and display when models originate from local vs remote manifests.
- Render prediction cards (per model + ensemble) with probability bars, logits, and manifest provenance badges plus a status panel showing loader health. Add draw/home/away bars and highlight the ensemble winner.
- Verify responsiveness + accessibility (keyboard navigation, screen-reader labels, focus outlines) and provide fallback text for small screens.
- Tests: React Testing Library coverage for selector component + results list, MSW-driven hook tests for success/error, and Playwright coverage for selecting teams via keyboard.

## Commit 6 – Attribution & Historical Insights
- Add tabs for Performance/Financial/Market feature families that display top/bottom SHAP contributors, including volatility warnings when values missing. Source data from static JSON caches generated during publish step and fall back to local cache paths when Kaggle artefacts aren’t available.
- Include LOO toggle chart showing delta when removing each signal family; highlight instability >5 percentage points.
- Create historical sparklines comparing last five predictions vs actuals per team (data from `/api/history` route backed by cached CSV slices).
- Tests: snapshot tests for SHAP visual components, contract tests for `/api/history`, end-to-end chart verification via Playwright screenshot assertions.

## Commit 7 – Auto-Update Workflow & Observability
- Wire `scripts/publish_model.py` into CI (GitHub Action / Kaggle notebook post-run) so manifest & artefacts upload automatically after retraining, and mirror the same entry point for local-only training sessions (e.g., watch a directory for new manifests).
- Add Vercel deploy hook + small CLI (`scripts/trigger_frontend_refresh.py`) invoking `/api/reload` with secret token as part of release pipeline.
- Instrument `/api/predict` with latency logging + error captures to Vercel Analytics; expose build/version info in footer.
- Verify reload path manually (invoke script, ensure new `run_id` surfaces in UI without redeploy).
- Tests: CI pipeline integration test (mocked secrets) ensuring hooks fire, logging assertions in unit tests, and manual smoke verifying `/api/reload` updates metadata.

## Commit 8 – Notebook Parity & Local Inference
- Refactor `Football Predictor Models.ipynb` to expose repeatable export helpers per model: export trained weights to ONNX/tfjs, serialize preprocessing state (feature order, scalers, encoders), and dump SHAP/LOO caches.
- Create a shared feature-store module (Python) that reproduces each notebook preprocessing pipeline using `Dataset_Version_7.csv` so fixture lookups return the exact feature vectors each model expects. Cache outputs locally for quick reuse.
- Build a local inference service (FastAPI/Node) or ONNX bindings inside the Next.js API that load the manifest, map feature vectors to tensors, and run all three models to produce real logits/probabilities instead of heuristics.
- Extend the manifest + publisher to reference preprocessing bundles and feature schema hashes; add regression tests comparing notebook predictions against the new service for a set of fixtures (tolerance thresholds).
- Tests: automated parity suite (Python) asserting API logits match notebook outputs, unit tests around feature-store transforms, and integration tests in `/api/predict` that load the exported models.
- **Scope Overview:** Mirror the notebook’s three pipelines (performance dense, financial dense, market odds) inside a reusable inference stack so local web/API calls match Kaggle results. Constraints: local-first (no Kaggle API), align with `Dataset_Version_7.csv`, reuse manifest workflow.
- **Export Layer:** Add notebook cells that (1) convert trained Keras models to TFJS/ONNX, (2) serialize preprocessing assets (feature order, scalers, rolling window caches), (3) persist SHAP/LOO caches, and (4) wrap all exports into helper functions (`export_performance_model(run_id, output_dir)`).
- **Shared Dataset Feature Store:** Maintain a Python module (`pipelines/feature_store.py`) that rebuilds performance/financial/market features from the dataset; add caching (Parquet/SQLite) to avoid recomputation and expose a CLI for fixture lookups.
- **Local Inference Service:** Provide a FastAPI or Node module that loads manifests, assembles feature tensors via the feature store, and runs ONNX/tfjs inference. `/api/predict` should call this service (or directly invoke `onnxruntime-node`) so each view’s predictions are real model outputs.
- **Manifest Enhancements:** Update `scripts/publish_model.py` + schema to accept preprocessing bundles, feature schema versions, and SHAP cache references. Validate that every manifest entry exists and matches expected checksums before publication.
- **Local Workflow:** Train notebook → run export helpers → publish manifest (local paths only) → start Next.js server pointed at the manifest so inference uses the exported models and latest dataset.
- **Validation Plan:** Add regression tests comparing notebook predictions vs API predictions for a shared fixture list, store golden JSON outputs, and ship a CLI (`pipelines/predict_fixture.py`) for analysts to sanity-check predictions.
- **Action Items:** Document export API, prototype feature store parity, finalize ONNX vs TFJS decision, and extend manifest validation to cover preprocessing bundles and schema hashes.

## Commit 9 – Documentation & Maintenance Playbook
- Extend `README.md` with front-end architecture overview, retrain→publish→reload instructions, and troubleshooting tips for both Kaggle-hosted and local-only workflows.
- Add `docs/run_registry.md` describing experiment tracking tables + links to Kaggle dataset versions.
- Update Kaggle notebook cells (if needed) to call publisher script and record metrics automatically.
- Final QA pass: `npm run lint`, `npm run test`, `npm run build`, `npm run test:e2e`, plus smoke test of API routes locally.

Keep this plan visible during development; every commit message should reference the section number to maintain traceability between spec and implementation.
