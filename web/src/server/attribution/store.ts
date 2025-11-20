import { attributionViews, AttributionView } from "@/data/attribution";

export function getAttributionView(view: string): AttributionView {
  const key = view.toLowerCase();
  return (
    attributionViews[key] ??
    attributionViews.performance
  );
}
