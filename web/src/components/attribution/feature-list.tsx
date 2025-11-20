"use client";

import type { FeatureContribution } from "@/data/attribution";

type Props = {
  title: string;
  items: FeatureContribution[];
};

export function FeatureList({ title, items }: Props) {
  return (
    <div className="rounded-2xl border border-white/5 bg-white/5 p-4">
      <p className="text-xs uppercase tracking-[0.35em] text-muted">{title}</p>
      <ul className="mt-3 space-y-3">
        {items.map((item) => (
          <li
            key={item.feature}
            className="space-y-1 rounded-xl bg-background/40 p-3"
          >
            <div className="flex items-center justify-between text-sm font-semibold text-foreground">
              <span>{item.feature}</span>
              <span>{item.value >= 0 ? "+" : ""}
                {Math.round(item.value * 100) / 100}</span>
            </div>
            <p className="text-xs text-muted">{item.description}</p>
          </li>
        ))}
      </ul>
    </div>
  );
}
