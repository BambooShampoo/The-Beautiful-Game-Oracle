#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 4 ]]; then
  cat <<'USAGE'
Usage: scripts/publish_and_refresh.sh RUN_ID DATASET_VERSION RELOAD_URL RELOAD_TOKEN [publish args...]

Example:
  scripts/publish_and_refresh.sh \
      2024-06-01-v7 \
      7 \
      https://oracle.vercel.app/api/reload \
      $RELOAD_TOKEN \
      --model performance_dense=export/perf/model.json:tfjs \
      --preprocessing scalers=export/shared/scalers.json \
      --attribution performance_shap=export/attrib/perf.npz
USAGE
  exit 1
fi

RUN_ID="$1"
DATASET_VERSION="$2"
RELOAD_URL="$3"
RELOAD_TOKEN="$4"
shift 4

echo "[publish] Building manifest for run ${RUN_ID} (dataset ${DATASET_VERSION})"
python scripts/publish_model.py \
  --run-id "${RUN_ID}" \
  --dataset-version "${DATASET_VERSION}" \
  "$@"

echo "[publish] Triggering frontend reload at ${RELOAD_URL}"
python scripts/trigger_frontend_refresh.py \
  --endpoint "${RELOAD_URL}" \
  --token "${RELOAD_TOKEN}"

echo "[publish] Done."
