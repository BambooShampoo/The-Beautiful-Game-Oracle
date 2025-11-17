import { randomUUID } from "node:crypto";

type PredictLogEvent = {
  id: string;
  timestamp: string;
  home: string;
  away: string;
  status: "success" | "error";
  runId?: string | null;
  datasetVersion?: string | number | null;
  durationMs?: number;
  error?: string;
};

const recentEvents: PredictLogEvent[] = [];
const MAX_EVENTS = 50;

export function logPredictSuccess(params: {
  home: string;
  away: string;
  runId?: string | null;
  datasetVersion?: string | number | null;
  durationMs?: number;
}) {
  pushEvent({
    id: randomUUID(),
    timestamp: new Date().toISOString(),
    status: "success",
    ...params,
  });
}

export function logPredictFailure(params: {
  home: string;
  away: string;
  error: string;
  runId?: string | null;
  datasetVersion?: string | number | null;
}) {
  pushEvent({
    id: randomUUID(),
    timestamp: new Date().toISOString(),
    status: "error",
    ...params,
  });
}

function pushEvent(event: PredictLogEvent) {
  recentEvents.unshift(event);
  if (recentEvents.length > MAX_EVENTS) {
    recentEvents.pop();
  }
  if (process.env.PREDICT_LOG_SILENT !== "1") {
    console.info("[predict-log]", JSON.stringify(event));
  }
}

export function getRecentPredictEvents() {
  return [...recentEvents];
}
