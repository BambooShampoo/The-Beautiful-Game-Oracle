"use client";

import { useEffect, useState } from "react";

export type LoaderStatus =
  | { status: "loading"; data: null; error: null }
  | { status: "ready"; data: StatusPayload; error: null }
  | { status: "error"; data: null; error: string };

type StatusPayload = {
  run_id: string | null;
  dataset_version: string | number | null;
  manifest_source: { value: string | null; kind: string | null };
  loaded_at: string | null;
};

export function useLoaderStatus() {
  const [state, setState] = useState<LoaderStatus>({
    status: "loading",
    data: null,
    error: null,
  });

  useEffect(() => {
    let cancelled = false;
    async function fetchStatus() {
      try {
        const res = await fetch("/api/status");
        const json = await res.json();
        if (!cancelled) {
          setState({
            status: "ready",
            data: {
              run_id: json.run_id ?? null,
              dataset_version: json.dataset_version ?? null,
              manifest_source: json.manifest_source ?? { value: null, kind: null },
              loaded_at: json.loaded_at ?? null,
            },
            error: null,
          });
        }
      } catch (error) {
        if (!cancelled) {
          setState({
            status: "error",
            data: null,
            error: (error as Error).message,
          });
        }
      }
    }
    fetchStatus();
    return () => {
      cancelled = true;
    };
  }, []);

  return state;
}
