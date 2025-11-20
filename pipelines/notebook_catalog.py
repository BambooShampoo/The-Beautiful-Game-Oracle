"""Utilities for syncing feature metadata from the latest notebook runs.

Training notebooks emit `metrics.json` with the feature columns used by each
view; this module walks the `artifacts/experiments` tree and exposes helpers
to map those files back into the Python feature store.
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence

LOGGER = logging.getLogger(__name__)

RUN_PREFIX = "run_"
METRICS_FILENAME = "metrics.json"
DEFAULT_EXPERIMENT_ROOT = Path("artifacts/experiments")


def _read_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _extract_dataset_version(dataset_label: Optional[str]) -> Optional[str]:
    if not dataset_label:
        return None
    match = re.search(r"(\d+)", str(dataset_label))
    if match:
        return match.group(1)
    return None


@dataclass(frozen=True)
class NotebookModelSpec:
    name: str
    feature_cols: Sequence[str]
    dataset_label: Optional[str]
    metrics_path: Path

    @property
    def dataset_version(self) -> Optional[str]:
        return _extract_dataset_version(self.dataset_label)


@dataclass
class NotebookRun:
    run_id: str
    path: Path
    models: Dict[str, NotebookModelSpec]

    @property
    def dataset_versions(self) -> List[str]:
        versions: List[str] = []
        for model in self.models.values():
            version = model.dataset_version
            if version and version not in versions:
                versions.append(version)
        return versions

    @property
    def feature_columns(self) -> Dict[str, Sequence[str]]:
        return {name: spec.feature_cols for name, spec in self.models.items()}

    @property
    def required_features(self) -> List[str]:
        unique: Dict[str, None] = {}
        for spec in self.models.values():
            for feature in spec.feature_cols:
                if feature not in unique:
                    unique[feature] = None
        return list(unique.keys())


def _is_run_dir(path: Path) -> bool:
    return path.is_dir() and path.name.startswith(RUN_PREFIX)


def _sorted_run_dirs(root: Path) -> List[Path]:
    run_dirs = [child for child in root.iterdir() if _is_run_dir(child)]
    run_dirs.sort(key=lambda p: p.name, reverse=True)
    return run_dirs


def _load_model_spec(model_dir: Path) -> Optional[NotebookModelSpec]:
    metrics_path = model_dir / METRICS_FILENAME
    if not metrics_path.exists():
        return None
    metrics = _read_json(metrics_path)
    feature_cols = metrics.get("feature_cols") or []
    if not isinstance(feature_cols, list):
        feature_cols = []
    dataset_label = metrics.get("dataset_label")
    return NotebookModelSpec(
        name=model_dir.name,
        feature_cols=list(feature_cols),
        dataset_label=dataset_label,
        metrics_path=metrics_path,
    )


def load_notebook_run(run_dir: Path, model_names: Optional[Iterable[str]] = None) -> NotebookRun:
    if not run_dir.exists():
        raise FileNotFoundError(f"Notebook run directory not found: {run_dir}")
    models: Dict[str, NotebookModelSpec] = {}
    names = list(model_names) if model_names else [child.name for child in run_dir.iterdir() if child.is_dir()]
    for name in names:
        model_dir = run_dir / name
        if not model_dir.exists():
            continue
        spec = _load_model_spec(model_dir)
        if spec:
            models[name] = spec
    return NotebookRun(run_id=run_dir.name, path=run_dir, models=models)


def discover_latest_notebook_run(
    root: Path = DEFAULT_EXPERIMENT_ROOT,
    model_names: Optional[Iterable[str]] = None,
) -> Optional[NotebookRun]:
    if not root.exists():
        LOGGER.warning("Experiment root %s does not exist", root)
        return None
    for run_dir in _sorted_run_dirs(root):
        run = load_notebook_run(run_dir, model_names=model_names)
        if run.models:
            LOGGER.debug("Discovered notebook run %s with models: %s", run.run_id, ", ".join(run.models))
            return run
    LOGGER.warning("No notebook runs with metrics found under %s", root)
    return None


def resolve_dataset_version(
    explicit_version: Optional[str],
    *,
    dataset_label: Optional[str] = None,
    fallback_versions: Optional[Sequence[str]] = None,
) -> Optional[str]:
    if explicit_version:
        return str(explicit_version)
    label_version = _extract_dataset_version(dataset_label)
    if label_version:
        return label_version
    if fallback_versions:
        for version in fallback_versions:
            if version:
                return str(version)
    return None
