"""CLI helpers to export trained models and preprocessing bundles from Jupyter."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Callable

import tensorflow as tf

from .export_artifacts import export_preprocessing_bundle, export_tfjs, save_onnx


def _dummy_model():
    model = tf.keras.Sequential(
        [
            tf.keras.layers.Input(shape=(8,)),
            tf.keras.layers.Dense(16, activation="relu"),
            tf.keras.layers.Dense(3, activation="linear"),
        ]
    )
    model.compile()
    return model


def export_dummy(output_dir: Path) -> None:
    model = _dummy_model()
    export_tfjs(model, output_dir / "tfjs")
    save_onnx(model, output_dir / "model.onnx")
    bundle = {
        "feature_names": [f"f{i}" for i in range(8)],
        "scaling": {"mean": [0.0] * 8, "std": [1.0] * 8},
    }
    export_preprocessing_bundle(bundle, output_dir / "preprocessing.json")


def main():
    parser = argparse.ArgumentParser(description="Export notebook artefacts.")
    parser.add_argument(
        "--output-dir",
        type=Path,
        required=True,
        help="Directory where model weights and preprocessing bundles will be stored.",
    )
    args = parser.parse_args()
    export_dummy(args.output_dir)
    print(f"Wrote dummy artefacts to {args.output_dir}")


if __name__ == "__main__":  # pragma: no cover
    main()
