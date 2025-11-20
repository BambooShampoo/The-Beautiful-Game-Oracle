from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.publish_model import (
    ResourceSpec,
    build_manifest,
    parse_args,
    validate_manifest,
    write_manifest,
)


def create_file(tmp_path: Path, relative: str, content: bytes = b"x") -> Path:
  path = tmp_path / relative
  path.parent.mkdir(parents=True, exist_ok=True)
  path.write_bytes(content)
  return path


def test_build_manifest_collects_sha_and_sizes(tmp_path: Path):
  model_file = create_file(tmp_path, "performance/model.json", b"model-bytes")
  scaler_file = create_file(tmp_path, "pre/scalers.json", b"{}")
  shap_file = create_file(tmp_path, "attrib/perf.npz", b"data")

  manifest = build_manifest(
      run_id="2024-05-20-v7",
      dataset_version="7",
      models=[ResourceSpec("performance_dense", model_file, resource_format="tfjs")],
      preprocessing_resources=[ResourceSpec("scalers", scaler_file)],
      attribution_resources=[ResourceSpec("perf_shap", shap_file, view="performance")],
      artefact_base_url="https://example.com/run",
      notes="smoke-test",
      local_root=tmp_path,
      prefer_relative_local_paths=True,
  )

  assert manifest["models"][0]["size_bytes"] == model_file.stat().st_size
  assert manifest["preprocessing"][0]["sha256"] is not None
  assert manifest["attribution"][0]["uri"].startswith("https://example.com/run")
  assert manifest["models"][0]["local_path"] == "performance/model.json"


def test_write_manifest_creates_file(tmp_path: Path):
  model_file = create_file(tmp_path, "m/model.bin")
  manifest = build_manifest(
      run_id="run-A",
      dataset_version="7",
      models=[ResourceSpec("performance_dense", model_file, resource_format="tfjs")],
      preprocessing_resources=[],
      attribution_resources=[],
      local_root=tmp_path,
      prefer_relative_local_paths=False,
  )
  path = write_manifest(manifest, tmp_path / "out", "run-A")
  assert path.exists()
  saved = json.loads(path.read_text())
  assert saved["run_id"] == "run-A"


def test_validate_manifest_uses_schema(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
  schema = {
      "$schema": "http://json-schema.org/draft-07/schema#",
      "type": "object",
      "required": ["run_id"],
  }
  schema_path = tmp_path / "schema.json"
  schema_path.write_text(json.dumps(schema))

  manifest = {"run_id": "abc"}
  validate_manifest(manifest, schema_path)


def test_parse_args_requires_models(monkeypatch: pytest.MonkeyPatch):
  with pytest.raises(SystemExit):
    parse_args(["--run-id", "abc"])
