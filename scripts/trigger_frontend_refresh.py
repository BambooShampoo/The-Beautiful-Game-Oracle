#!/usr/bin/env python3
"""
Trigger the frontend reload endpoint so Vercel picks up freshly published manifests.

Usage:
    python scripts/trigger_frontend_refresh.py \
        --endpoint https://oracle.vercel.app/api/reload \
        --token $RELOAD_TOKEN
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from typing import Optional

import urllib.request
import urllib.error


@dataclass
class ReloadResult:
  status: int
  body: dict


def trigger_reload(endpoint: str, token: str, timeout: int = 15) -> ReloadResult:
  request = urllib.request.Request(
      endpoint,
      method="POST",
      headers={
          "Content-Type": "application/json",
          "x-reload-token": token,
      },
  )
  try:
    with urllib.request.urlopen(request, timeout=timeout) as response:
      data = response.read().decode("utf-8")
      return ReloadResult(
          status=response.status,
          body=json.loads(data or "{}"),
      )
  except urllib.error.HTTPError as exc:
    try:
      payload = exc.read().decode("utf-8")
      body = json.loads(payload or "{}")
    except Exception:
      body = {"error": exc.reason}
    return ReloadResult(status=exc.code, body=body)
  except urllib.error.URLError as exc:
    raise RuntimeError(f"Failed to reach reload endpoint: {exc}") from exc


def parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
  parser = argparse.ArgumentParser(
      description="Call the frontend reload endpoint after publishing new manifests.",
  )
  parser.add_argument(
      "--endpoint",
      required=True,
      help="Reload endpoint URL (e.g., https://oracle.vercel.app/api/reload).",
  )
  parser.add_argument(
      "--token",
      required=True,
      help="Reload token matching the serverless function secret.",
  )
  return parser.parse_args(argv)


def main(argv: Optional[list[str]] = None) -> None:
  args = parse_args(argv)
  result = trigger_reload(args.endpoint, args.token)
  if result.status != 200 or not result.body.get("ok"):
    raise SystemExit(
        f"Reload failed (status={result.status}): {result.body.get('error')}"
    )
  print(
      f"Reloaded to run_id={result.body.get('run_id')} "
      f"at {result.body.get('reloaded_at')}",
  )


if __name__ == "__main__":  # pragma: no cover
  main(sys.argv[1:])
