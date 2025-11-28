# Data & Model Update Guide

This guide explains how to update the dataset and machine learning models for the **The Beautiful Game Oracle** web application.

## 1. Updating the Dataset

The web app uses a CSV dataset (e.g., `Dataset_Version_7.csv`) and a financial dataset (`financial_dataset.csv`).

### Steps:
1.  **Generate/Obtain the new dataset**:
    *   Ensure you have the new CSV file (e.g., `Dataset_Version_8.csv`).
    *   Ensure you have the updated `financial_dataset.csv`.

2.  **Place files in the web directory**:
    *   Copy the main dataset to `web/public/data/`.
    *   Copy `financial_dataset.csv` to `web/public/data/`.
    *   *Note*: If you have a `team_cache` directory, update it in `web/public/data/team_cache` as well. This is for club names for the team dropdown.

3.  **Update Configuration**:
    *   Open `web/.env.local` (for local dev) and Vercel Environment Variables (for production).
    *   Update `FEATURE_DATASET_VERSION` to the new version number (e.g., `8`).
    *   *Alternatively*, if you are not using the env var, ensure the code defaults to the correct version in `web/src/config/env.ts`.

4.  **Deploy**:
    *   Commit the new data files to the repository.
    *   Push to `main` to trigger a deployment (or run `vercel deploy --prod`).

---

## 2. Updating Models (ONNX)

The web app loads ONNX models and their preprocessing JSON bundles. **Crucially**, to avoid Vercel size limits, these files are loaded remotely from GitHub Raw URLs.

### Steps:
1.  **Export new models**:
    *   Run your training/export scripts.
    *   **Specific Script**: The script `pipelines/export_xgb_onnx.py` is used to convert the trained XGBoost models to ONNX format.
        *   Usage: `python pipelines/export_xgb_onnx.py <run_dir> --output <output_dir>`
    *   Ensure the output files (e.g., `performance_dense.onnx`, `performance_dense_preprocessing.json`, etc.) are saved in `artifacts/run_export/` (or your preferred location).

2.  **Commit and Push**:
    *   **You MUST commit and push these new model files to the GitHub repository.**
    *   The web app fetches them from `https://raw.githubusercontent.com/Beautiful-Game-Oracle/The-Beautiful-Game-Oracle/main/...`.
    *   If you don't push them, the web app will continue to load the old models (or fail if the paths change).

3.  **Update Manifest (`dev.json`)**:
    *   Open `web/public/fixtures/dev.json`.
    *   Update the `uri` fields for each model and preprocessing bundle to point to the new raw URLs.
        *   *Example*: `https://raw.githubusercontent.com/Beautiful-Game-Oracle/The-Beautiful-Game-Oracle/main/artifacts/run_export/performance_dense.onnx`
    *   Update the `sha256` and `size_bytes` fields if you want to be precise (though the app currently relies on the URI).
    *   Update `run_id` and `trained_at` metadata.

4.  **Deploy**:
    *   Commit the changes to `dev.json`.
    *   Push to `main`.

---

## Summary Checklist
- [ ] New dataset CSV in `web/public/data/`
- [ ] New `financial_dataset.csv` in `web/public/data/`
- [ ] New ONNX models and JSONs in `artifacts/run_export/`
- [ ] **Git Push** all new files to `main`.
- [ ] Update `FEATURE_DATASET_VERSION` (env var).
- [ ] Update `web/public/fixtures/dev.json` (URIs and metadata).
- [ ] Redeploy.
