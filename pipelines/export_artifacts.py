"""Utilities to export trained notebook models + preprocessing bundles."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict

import tensorflow as tf

try:
    import tensorflowjs as tfjs  # type: ignore
except ImportError:  # pragma: no cover
    tfjs = None


def export_tfjs(model: tf.keras.Model, output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    if tfjs is None:
        raise RuntimeError("tensorflowjs not installed; pip install tensorflowjs")
    tfjs.converters.save_keras_model(model, str(output_dir))
    return output_dir


def export_preprocessing_bundle(bundle: Dict, output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as fh:
        json.dump(bundle, fh, indent=2)
    return output_path


def save_onnx(model: tf.keras.Model, output_path: Path) -> Path:
    import tf2onnx  # type: ignore

    spec = (tf.TensorSpec(model.inputs[0].shape, tf.float32, name="input"),)
    model_proto, _ = tf2onnx.convert.from_keras(model, input_signature=spec)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("wb") as fh:
        fh.write(model_proto.SerializeToString())
    return output_path
