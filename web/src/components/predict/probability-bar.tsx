"use client";

type Props = {
  label: string;
  value: number;
  highlight?: boolean;
};

export function ProbabilityBar({ label, value, highlight }: Props) {
  const pct = Math.round(value * 1000) / 10;
  return (
    <div className="space-y-1">
      <div className="flex items-center justify-between text-xs font-semibold uppercase tracking-wide text-muted">
        <span>{label}</span>
        <span>{pct.toFixed(1)}%</span>
      </div>
      <div className="h-2 rounded-full bg-white/5">
        <div
          className="h-full rounded-full bg-brand transition-all"
          style={{
            width: `${Math.min(100, Math.max(0, pct))}%`,
            opacity: highlight ? 1 : 0.7,
          }}
        />
      </div>
    </div>
  );
}
