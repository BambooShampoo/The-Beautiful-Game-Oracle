#!/usr/bin/env python3
"""
Package model artefacts and emit a manifest that downstream deployments can trust.

Usage (dry run):
    python scripts/publish_model.py \
        --run-id 2024-05-20-v7 \
        --dataset-version 7 \
        --model performance_dense=tests/fixtures/performance/model.json:tfjs \
        --model financial_dense=tests/fixtures/financial/model.onnx:onnx \
        --preprocessing scalers=tests/fixtures/shared/scalers.json \
        --attribution performance_shap=tests/fixtures/attrib/perf_shap.npz \
        --output-dir artifacts/manifests \
        --local-root . \
        --local-path-mode relative \
        --dry-run
"""

from __future__ import annotations

import argparse
import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from typing import Iterable, List, Optional


def _read_json(path: Path) -> dict:
  with path.open("r", encoding="utf-8") as fh:
    return json.load(fh)


def _compute_sha256(path: Path) -> str:
  digest = sha256()
  with path.open("rb") as fh:
    for chunk in iter(lambda: fh.read(65536), b""):
      digest.update(chunk)
  return digest.hexdigest()


def _ensure_exists(path: Path, kind: str) -> None:
  if not path.exists():
    raise FileNotFoundError(f"{kind} path does not exist: {path}")
  if path.is_dir():
    raise IsADirectoryError(f"{kind} path must be a file, got directory: {path}")


@dataclass
class ResourceSpec:
  identifier: str
  path: Path
  resource_format: Optional[str] = None
  view: Optional[str] = None

  def _compute_local_path(
      self, local_root: Optional[Path], prefer_relative: bool
  ) -> str:
    path_str = str(self.path)
    if local_root:
      try:
        relative = self.path.relative_to(local_root)
        return str(relative) if prefer_relative else path_str
      except ValueError:
        return path_str
    return path_str

  def to_manifest_entry(
      self,
      *,
      base_url: Optional[str] = None,
      local_root: Optional[Path] = None,
      prefer_relative: bool = True,
  ) -> dict:
    _ensure_exists(self.path, self.identifier)
    entry = {
        "id": self.identifier,
        "path": str(self.path),
        "local_path": self._compute_local_path(local_root, prefer_relative),
        "sha256": _compute_sha256(self.path),
        "size_bytes": self.path.stat().st_size,
    }
    if self.resource_format:
      entry["format"] = self.resource_format
    if self.view:
      entry["view"] = self.view
    if base_url:
      relative_name = self.path.name
      entry["uri"] = f"{base_url.rstrip('/')}/{relative_name}"
    return entry


def _parse_resource_arg(entry: str, allow_format: bool) -> ResourceSpec:
  if "=" not in entry:
    raise ValueError(f"Resource entry must match name=path[:format], got: {entry}")
  name, remainder = entry.split("=", 1)
  fmt = None
  if allow_format and ":" in remainder:
    remainder, fmt = remainder.rsplit(":", 1)
  path = Path(remainder).expanduser().resolve()
  return ResourceSpec(identifier=name.strip(), path=path, resource_format=fmt)


def build_manifest(
    run_id: str,
    dataset_version: str,
    models: Iterable[ResourceSpec],
    preprocessing_resources: Iterable[ResourceSpec],
    attribution_resources: Iterable[ResourceSpec],
    *,
    artefact_base_url: Optional[str] = None,
    metrics: Optional[dict] = None,
    notes: Optional[str] = None,
    trained_at: Optional[str] = None,
    feature_schema_version: Optional[str] = None,
    local_root: Optional[Path] = None,
    prefer_relative_local_paths: bool = True,
) -> dict:
  model_entries = [
      spec.to_manifest_entry(
          base_url=artefact_base_url,
          local_root=local_root,
          prefer_relative=prefer_relative_local_paths,
      )
      for spec in models
  ]
  if not model_entries:
    raise ValueError("At least one --model entry is required.")

  preprocessing_entries = [
      spec.to_manifest_entry(
          base_url=artefact_base_url,
          local_root=local_root,
          prefer_relative=prefer_relative_local_paths,
      )
      for spec in preprocessing_resources
  ]
  attribution_entries = [
      spec.to_manifest_entry(
          base_url=artefact_base_url,
          local_root=local_root,
          prefer_relative=prefer_relative_local_paths,
      )
      for spec in attribution_resources
  ]

  manifest = {
      "run_id": run_id,
      "dataset_version": dataset_version,
      "trained_at": trained_at
      or datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
      "models": model_entries,
      "preprocessing": preprocessing_entries,
      "attribution": attribution_entries,
  }
  if metrics:
    manifest["metrics"] = metrics
  if notes:
    manifest["notes"] = notes
  if artefact_base_url:
    manifest["artefact_base_url"] = artefact_base_url
  if feature_schema_version:
    manifest["feature_schema_version"] = feature_schema_version

  return manifest


def validate_manifest(manifest: dict, schema_path: Path) -> None:
  schema = _read_json(schema_path)
  try:
    import jsonschema  # type: ignore
  except ModuleNotFoundError as exc:  # pragma: no cover - guard rails
    raise RuntimeError(
        "jsonschema is required for validation. Run `pip install jsonschema`."
    ) from exc
  jsonschema.validate(instance=manifest, schema=schema)


def write_manifest(manifest: dict, output_dir: Path, run_id: str) -> Path:
  output_dir.mkdir(parents=True, exist_ok=True)
  manifest_path = (output_dir / f"{run_id}.json").resolve()
  with manifest_path.open("w", encoding="utf-8") as fh:
    json.dump(manifest, fh, indent=2, sort_keys=True)
    fh.write("\n")
  return manifest_path


def _load_metrics(path: Optional[Path]) -> Optional[dict]:
  if path is None:
    return None
  _ensure_exists(path, "metrics")
  return _read_json(path)


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
  parser = argparse.ArgumentParser(
      description="Publish model artefacts into a manifest.",
      formatter_class=argparse.ArgumentDefaultsHelpFormatter,
  )
  parser.add_argument("--run-id", required=True, help="Unique identifier for this run.")
  parser.add_argument(
      "--dataset-version",
      default="7",
      help="Dataset version number/tag used for training.",
  )
  parser.add_argument(
      "--model",
      action="append",
      default=[],
      required=True,
      help="Model artefact spec: name=path[:format]. Provide once per model.",
  )
  parser.add_argument(
      "--preprocessing",
      action="append",
      default=[],
      help="Preprocessing resource spec: name=path.",
  )
  parser.add_argument(
      "--attribution",
      action="append",
      default=[],
      help="Attribution cache spec: name=path.",
  )
  parser.add_argument(
      "--artefact-base-url",
      help="Optional base URL prefix where artefacts will live (e.g., Kaggle dataset URL).",
  )
  parser.add_argument(
      "--local-root",
      type=Path,
      default=Path(".").resolve(),
      help="Base directory used to compute relative local paths in the manifest.",
  )
  parser.add_argument(
      "--local-path-mode",
      choices=["relative", "absolute"],
      default="relative",
      help="How to emit local_path entries relative to --local-root.",
  )
  parser.add_argument(
      "--metrics-file",
      type=Path,
      help="Optional JSON file containing evaluation metrics to embed in the manifest.",
  )
  parser.add_argument(
      "--notes",
      help="Optional freeform notes stored alongside the manifest.",
  )
  parser.add_argument(
      "--feature-schema-version",
      help="Feature preprocessing schema version (aligns with dataset transformations).",
  )
  parser.add_argument(
      "--trained-at",
      help="Override training timestamp (ISO8601). Defaults to now in UTC.",
  )
  parser.add_argument(
      "--manifest-schema",
      type=Path,
      default=Path("artifacts/manifest_schema.json"),
      help="Path to the manifest JSON schema for validation.",
  )
  parser.add_argument(
      "--output-dir",
      type=Path,
      default=Path("artifacts/manifests"),
      help="Directory where the manifest will be written.",
  )
  parser.add_argument(
      "--dry-run",
      action="store_true",
      help="Print the manifest instead of writing it to disk.",
  )
  return parser.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> None:
  args = parse_args(argv)
  model_specs = [
      _parse_resource_arg(entry, allow_format=True) for entry in args.model
  ]
  preprocessing_specs = [
      _parse_resource_arg(entry, allow_format=False) for entry in args.preprocessing
  ]
  attribution_specs = [
      _parse_resource_arg(entry, allow_format=False) for entry in args.attribution
  ]

  manifest = build_manifest(
      run_id=args.run_id,
      dataset_version=str(args.dataset_version),
      models=model_specs,
      preprocessing_resources=preprocessing_specs,
      attribution_resources=attribution_specs,
      artefact_base_url=args.artefact_base_url,
      metrics=_load_metrics(args.metrics_file),
      notes=args.notes,
      trained_at=args.trained_at,
      feature_schema_version=args.feature_schema_version,
      local_root=args.local_root,
      prefer_relative_local_paths=args.local_path_mode == "relative",
  )
  validate_manifest(manifest, args.manifest_schema)

  if args.dry_run:
    json.dump(manifest, fp=os.sys.stdout, indent=2, sort_keys=True)
    os.sys.stdout.write("\n")
    return

  manifest_path = write_manifest(manifest, args.output_dir, args.run_id)
  print(f"Wrote manifest to {manifest_path}")


if __name__ == "__main__":  # pragma: no cover
  main()
