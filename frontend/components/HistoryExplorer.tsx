"use client";

import { useMemo, useState } from "react";

import { DataTable } from "@/components/ui/DataTable";
import { StatTile } from "@/components/ui/StatTile";
import type { BacktestPrediction } from "@/lib/api";
import { pct } from "@/lib/features";

type Result = "all" | "correct" | "wrong";
type SortKey = "date" | "confidence-desc" | "confidence-asc";

const PAGE_SIZE = 50;

const selectClass =
  "rounded-lg border border-border bg-background px-3 py-2 text-sm focus:border-foreground focus:outline-none";

export function HistoryExplorer({
  predictions,
}: {
  predictions: BacktestPrediction[];
}) {
  const seasons = useMemo(
    () => [...new Set(predictions.map((p) => p.test_season))].sort(),
    [predictions],
  );

  const [season, setSeason] = useState<number | "all">("all");
  const [result, setResult] = useState<Result>("all");
  const [sort, setSort] = useState<SortKey>("date");
  const [visible, setVisible] = useState(PAGE_SIZE);

  const filtered = useMemo(() => {
    const rows = predictions.filter(
      (p) =>
        (season === "all" || p.test_season === season) &&
        (result === "all" || (result === "correct") === Boolean(p.correct)),
    );

    return rows.sort((a, b) => {
      if (sort === "confidence-desc") return b.confidence - a.confidence;
      if (sort === "confidence-asc") return a.confidence - b.confidence;
      return a.game_date.localeCompare(b.game_date);
    });
  }, [predictions, season, result, sort]);

  const correct = filtered.filter((p) => p.correct).length;
  const homeWins = filtered.filter((p) => p.home_score > p.away_score).length;
  const accuracy = filtered.length ? correct / filtered.length : 0;
  const baseline = filtered.length ? homeWins / filtered.length : 0;

  // Reset paging whenever the filter changes.
  function update<T>(setter: (v: T) => void) {
    return (value: T) => {
      setter(value);
      setVisible(PAGE_SIZE);
    };
  }

  return (
    <div>
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4 mb-8">
        <StatTile label="Games" value={filtered.length.toLocaleString()} />
        <StatTile
          label="Accuracy"
          value={filtered.length ? pct(accuracy) : "—"}
          sublabel={`${correct.toLocaleString()} correct`}
        />
        <StatTile
          label="Baseline"
          value={filtered.length ? pct(baseline) : "—"}
          sublabel="always pick home"
        />
        <StatTile
          label="Avg. confidence"
          value={
            filtered.length
              ? pct(
                  filtered.reduce((s, p) => s + p.confidence, 0) /
                    filtered.length,
                )
              : "—"
          }
        />
      </div>

      <div className="mb-4 flex flex-wrap gap-3">
        <select
          aria-label="Season"
          className={selectClass}
          value={season}
          onChange={(e) =>
            update(setSeason)(e.target.value === "all" ? "all" : Number(e.target.value))
          }
        >
          <option value="all">All seasons</option>
          {seasons.map((s) => (
            <option key={s} value={s}>
              {s}
            </option>
          ))}
        </select>
        <select
          aria-label="Result"
          className={selectClass}
          value={result}
          onChange={(e) => update(setResult)(e.target.value as Result)}
        >
          <option value="all">All results</option>
          <option value="correct">Correct only</option>
          <option value="wrong">Wrong only</option>
        </select>
        <select
          aria-label="Sort"
          className={selectClass}
          value={sort}
          onChange={(e) => update(setSort)(e.target.value as SortKey)}
        >
          <option value="date">Sort: date</option>
          <option value="confidence-desc">Sort: most confident</option>
          <option value="confidence-asc">Sort: least confident</option>
        </select>
      </div>

      <DataTable
        rowKey={(p) => p.game_id}
        rows={filtered.slice(0, visible)}
        columns={[
          { header: "Season", render: (p) => p.test_season },
          { header: "Wk", render: (p) => p.week, align: "right" },
          { header: "Date", render: (p) => p.game_date },
          { header: "Matchup", render: (p) => `${p.away_team} @ ${p.home_team}` },
          {
            header: "Pick",
            render: (p) => (p.predicted_home_win ? p.home_team : p.away_team),
          },
          {
            header: "Confidence",
            render: (p) => pct(p.confidence),
            align: "right",
          },
          {
            header: "Final",
            render: (p) => `${p.away_score}–${p.home_score}`,
            align: "right",
          },
          {
            header: "Result",
            render: (p) => (p.correct ? "✓ Correct" : "✗ Wrong"),
            align: "right",
          },
        ]}
      />

      <div className="mt-4 flex items-center justify-between text-xs text-muted">
        <span>
          Showing {Math.min(visible, filtered.length).toLocaleString()} of{" "}
          {filtered.length.toLocaleString()}
        </span>
        {visible < filtered.length && (
          <button
            type="button"
            onClick={() => setVisible((v) => v + PAGE_SIZE)}
            className="rounded-full border border-border px-4 py-1.5 text-foreground transition-colors hover:border-foreground"
          >
            Show more
          </button>
        )}
      </div>
    </div>
  );
}
