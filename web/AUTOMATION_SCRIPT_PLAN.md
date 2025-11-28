# Automated Asset Update Script Plan

This document outlines the requirements and logic for a Python script (`scripts/update_web_assets.py`) to automate the process of updating datasets and models for the web application.

## Goal
To streamline the deployment of new training runs by automatically copying files to the correct locations, calculating metadata (hashes/sizes), and updating the manifest file.

## Requirements
- Python 3.x
- Git (for pushing changes)

## Script Logic

### 1. Inputs
The script should accept the following arguments (or use configuration/defaults):
- `--run-dir`: Path to the directory containing the new model exports (default: `artifacts/run_export`).
- `--dataset`: Path to the new dataset CSV file.
- `--financial-dataset`: Path to the new financial dataset CSV file.
- `--version`: The new dataset version number (e.g., `8`).

### 2. File Operations
- **Dataset**:
    - Copy `--dataset` to `web/public/data/Dataset_Version_{version}.csv`.
    - Copy `--financial-dataset` to `web/public/data/financial_dataset.csv`.
- **Models**:
    - Ensure model files (`*.onnx`, `*.json`) are in `artifacts/run_export/`.
    - (If the training script outputs elsewhere, copy them to `artifacts/run_export/`).

### 3. Metadata Calculation
For each model and preprocessing file:
- Calculate **SHA256** hash.
- Get **File Size** (bytes).

### 4. Manifest Update (`web/public/fixtures/dev.json`)
- Read the existing `dev.json`.
- Update the `models` list:
    - For each model ID (e.g., `performance_dense`), update:
        - `sha256`
        - `size_bytes`
        - `uri`: `https://raw.githubusercontent.com/Beautiful-Game-Oracle/The-Beautiful-Game-Oracle/main/artifacts/run_export/{filename}`
- Update the `preprocessing` list:
    - Similar updates for preprocessing JSONs.
- Update global metadata:
    - `dataset_version`: Set to `--version`.
    - `trained_at`: Set to current timestamp (ISO 8601).
- Save `dev.json`.

### 5. Git Operations (Optional but Recommended)
- `git add web/public/data web/public/fixtures/dev.json artifacts/run_export`
- `git commit -m "chore: update web assets for version {version}"`
- `git push origin main`

## Example Usage
```bash
python scripts/update_web_assets.py \
  --run-dir ./experiments/run_20251128/export \
  --dataset ./data/processed/Dataset_Version_8.csv \
  --financial-dataset ./data/processed/financial_dataset.csv \
  --version 8
```

## Next Steps
1.  Implement this script in `scripts/update_web_assets.py`.
2.  Integrate it into the training pipeline (e.g., run automatically after training).
