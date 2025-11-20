import json
from pathlib import Path

import jsonschema
import pytest

SCHEMA_PATH = Path("artifacts/manifest_schema.json")
SCHEMA = json.loads(SCHEMA_PATH.read_text())


def _valid_manifest():
  return {
      "run_id": "2024-05-20-v7",
      "dataset_version": "7",
      "trained_at": "2024-05-20T12:00:00Z",
      "models": [
          {
              "id": "performance_dense",
              "format": "tfjs",
              "local_path": "performance/model.json",
              "path": "performance/model.json",
              "uri": "https://example.com/performance/model.json",
              "size_bytes": 123,
              "sha256": "a" * 64,
          }
      ],
      "preprocessing": [
          {
              "id": "scalers",
              "local_path": "pre/scalers.json",
              "path": "pre/scalers.json",
              "size_bytes": 50,
              "sha256": "b" * 64,
          }
      ],
      "attribution": [
          {
              "id": "performance_shap",
              "local_path": "attrib/perf.npz",
              "path": "attrib/perf.npz",
              "size_bytes": 80,
              "sha256": "c" * 64,
              "view": "performance",
          }
      ],
  }


def test_valid_manifest_passes_schema_validation():
  manifest = _valid_manifest()
  jsonschema.validate(instance=manifest, schema=SCHEMA)


def test_missing_models_fails_validation():
  manifest = _valid_manifest()
  manifest["models"] = []
  with pytest.raises(jsonschema.ValidationError):
    jsonschema.validate(instance=manifest, schema=SCHEMA)
