"""Patch manifest entries for new ONNX exports and preprocessing bundles."""
import argparse
import json
from pathlib import Path


def patch_manifest(manifest_path: Path, run_id: str) -> None:
    data = json.loads(manifest_path.read_text())
    data["run_id"] = run_id
    models = [
        {
            "id": "performance_dense",
            "format": "onnx",
            "path": "artifacts/run_export/performance/model.onnx",
            "local_path": "artifacts/run_export/performance/model.onnx",
            "sha256": "PLACEHOLDER",
            "size_bytes": 0,
        },
        {
            "id": "financial_dense",
            "format": "onnx",
            "path": "artifacts/run_export/financial/model.onnx",
            "local_path": "artifacts/run_export/financial/model.onnx",
            "sha256": "PLACEHOLDER",
            "size_bytes": 0,
        },
        {
            "id": "market_odds",
            "format": "onnx",
            "path": "artifacts/run_export/market/model.onnx",
            "local_path": "artifacts/run_export/market/model.onnx",
            "sha256": "PLACEHOLDER",
            "size_bytes": 0,
        }
    ]
    data["models"] = models
    data["preprocessing"] = [
        {
            "id": "performance_dense_preprocessing",
            "path": "artifacts/run_export/performance/preprocessing.json",
            "local_path": "artifacts/run_export/performance/preprocessing.json",
            "sha256": "PLACEHOLDER",
            "size_bytes": 0,
        },
        {
            "id": "financial_dense_preprocessing",
            "path": "artifacts/run_export/financial/preprocessing.json",
            "local_path": "artifacts/run_export/financial/preprocessing.json",
            "sha256": "PLACEHOLDER",
            "size_bytes": 0,
        },
        {
            "id": "market_odds_preprocessing",
            "path": "artifacts/run_export/market/preprocessing.json",
            "local_path": "artifacts/run_export/market/preprocessing.json",
            "sha256": "PLACEHOLDER",
            "size_bytes": 0,
        }
    ]
    manifest_path.write_text(json.dumps(data, indent=2))
    print(f"Patched manifest at {manifest_path}")


def main():
    parser = argparse.ArgumentParser(description="Patch manifest for new run")
    parser.add_argument("manifest", type=Path)
    parser.add_argument("run_id")
    args = parser.parse_args()
    patch_manifest(args.manifest, args.run_id)


if __name__ == '__main__':
    main()
