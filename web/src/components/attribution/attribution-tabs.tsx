"use client";

import { useState } from "react";

import { attributionViews } from "@/data/attribution";
import { Card, CardBody, CardTitle } from "@/components/ui/card";

import { FeatureList } from "./feature-list";
import { LooList } from "./loo-list";

const viewOrder = [
  { id: "performance", label: "Performance" },
  { id: "financial", label: "Financial" },
  { id: "market", label: "Market" },
];

export function AttributionTabs() {
  const [activeView, setActiveView] = useState("performance");
  const view = attributionViews[activeView];

  return (
    <Card className="bg-panel/80">
      <CardTitle className="flex items-center justify-between text-xl">
        Attribution Insights
        <div className="flex gap-2 text-xs">
          {viewOrder.map((tab) => (
            <button
              key={tab.id}
              type="button"
              onClick={() => setActiveView(tab.id)}
              className={`rounded-full px-3 py-1 font-semibold transition ${
                tab.id === activeView
                  ? "bg-brand text-black"
                  : "bg-white/5 text-muted hover:bg-white/10"
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </CardTitle>
      <CardBody className="mt-4 grid gap-4 lg:grid-cols-2">
        <FeatureList
          title="Top signals"
          items={view.topContributors}
        />
        <FeatureList
          title="Drag factors"
          items={view.negativeContributors}
        />
      </CardBody>
      <div className="mt-5">
        <LooList entries={view.loo} />
      </div>
    </Card>
  );
}
