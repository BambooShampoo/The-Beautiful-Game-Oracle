"use client";

type Props = {
  entries: Array<{ signal: string; delta: number }>;
};

export function LooList({ entries }: Props) {
  return (
    <div className="rounded-2xl border border-brand/10 bg-brand/5 p-4">
      <p className="text-xs uppercase tracking-[0.35em] text-muted">
        LOO impact
      </p>
      <ul className="mt-2 space-y-2">
        {entries.map((entry) => (
          <li
            key={entry.signal}
            className="flex items-center justify-between rounded-xl bg-white/10 px-3 py-2 text-sm"
          >
            <span>{entry.signal}</span>
            <span
              className={entry.delta <= 0 ? "text-danger" : "text-brand"}
            >
              {entry.delta.toFixed(3)}
            </span>
          </li>
        ))}
      </ul>
    </div>
  );
}
