"use client";

import { AttributionTabs } from "@/components/attribution/attribution-tabs";
import { PredictionDashboard } from "@/components/predict/prediction-dashboard";

export function PredictionWorkspace() {
  return (
    <main>
      <div className="mx-auto flex min-h-screen max-w-6xl flex-col gap-12 px-6 py-16 md:px-12">
        <PredictionDashboard />
        <section className="grid gap-6">
          <AttributionTabs />
        </section>
      </div>
    </main>
  );
}
