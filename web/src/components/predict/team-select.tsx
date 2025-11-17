"use client";

import type { ChangeEvent } from "react";
import { useEffect, useId, useMemo, useState } from "react";

import { getTeamProfile } from "@/data/teamMetadata";
import { cn } from "@/lib/cn";
import type { TeamOption } from "@/components/predict/use-team-options";

// TeamSelect renders a search input bound to the team roster returned by useTeamOptions.

type Props = {
  label: string;
  value: string;
  onChange: (value: string) => void;
  disabled?: boolean;
  teams: TeamOption[];
};

export function TeamSelect({ label, value, onChange, disabled, teams }: Props) {
  const selectedTeam =
    teams.find((team) => team.canonical === value) ?? null;
  const profile = value ? getTeamProfile(value) : null;
  const [query, setQuery] = useState(() => selectedTeam?.name ?? "");
  const listId = useId();

  useEffect(() => {
    if (selectedTeam) {
      setQuery(selectedTeam.name);
    }
  }, [selectedTeam]);

  const crestUrl = selectedTeam?.crest ?? profile?.crest ?? null;
  const filteredTeams = useMemo(() => {
    if (!query) return teams;
    const lower = query.toLowerCase();
    return teams.filter(
      (team) =>
        team.name.toLowerCase().includes(lower) ||
        team.shortName.toLowerCase().includes(lower) ||
        team.aliases.some((alias) => alias.toLowerCase().includes(lower)),
    );
  }, [query, teams]);

  function handleInputChange(event: ChangeEvent<HTMLInputElement>) {
    const next = event.target.value;
    setQuery(next);
    const match =
      teams.find(
        (team) =>
          team.name.toLowerCase() === next.toLowerCase() ||
          team.shortName.toLowerCase() === next.toLowerCase() ||
          team.aliases.some((alias) => alias.toLowerCase() === next.toLowerCase()),
      ) ?? null;
    if (match) {
      setQuery(match.name);
      onChange(match.canonical);
    }
  }

  return (
    <div className="flex w-full flex-col gap-3 text-sm font-medium text-muted">
      <label
        htmlFor={listId}
        className="flex flex-col gap-1"
      >
        <span>{label}</span>
        <div className="rounded-2xl border border-white/10 bg-surface/70 px-4 py-3 shadow-inner shadow-black/20 focus-within:border-brand/70 focus-within:ring-2 focus-within:ring-brand/40">
          <input
            id={listId}
            list={`${listId}-list`}
            value={query}
            onChange={handleInputChange}
            disabled={disabled}
            placeholder="Search Premier League clubs"
            className={cn(
              "w-full bg-transparent text-base text-foreground placeholder:text-muted focus:outline-none",
            )}
          />
        </div>
      </label>

      <datalist id={`${listId}-list`}>
        {filteredTeams.map((team) => (
          <option
            key={team.canonical}
            value={team.name}
          >
            {team.shortName}
          </option>
        ))}
      </datalist>

      {teams.length === 0 ? (
        <p className="text-xs text-muted">Loading club roster…</p>
      ) : selectedTeam ? (
        <div className="flex items-center gap-3 rounded-2xl border border-white/5 bg-white/5 px-4 py-2 text-xs text-muted">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          {crestUrl ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img
              src={crestUrl}
              alt={`${selectedTeam.name} crest`}
              className="h-10 w-10 rounded-full bg-white/10 p-1"
            />
          ) : (
            <div className="flex h-10 w-10 items-center justify-center rounded-full bg-white/10 text-base font-semibold text-foreground">
              {selectedTeam.shortName}
            </div>
          )}
          <div>
            <p className="text-base font-semibold text-foreground">
              {selectedTeam.name}
            </p>
            <p className="text-xs uppercase tracking-[0.3em]">{selectedTeam.shortName}</p>
          </div>
        </div>
      ) : (
        <p className="text-xs text-danger">
          Team not recognized. Try typing the full club name.
        </p>
      )}
    </div>
  );
}
