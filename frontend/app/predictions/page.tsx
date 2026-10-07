import Link from "next/link";

import { Card } from "@/components/ui/Card";
import { DataTable } from "@/components/ui/DataTable";
import { PageHeader } from "@/components/ui/PageHeader";
import { StatTile } from "@/components/ui/StatTile";
import {
  getPredictionStatus,
  getPredictionWeeks,
  getWeeklyPredictions,
  type PredictionRun,
  type WeeklyGame,
} from "@/lib/api";
import { featureLabel, pct } from "@/lib/features";

export const dynamic = "force-dynamic";

function StatusBanner({ run }: { run: PredictionRun }) {
  return (
    <Card className="mb-8">
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <h2 className="text-sm font-medium">
          {run.season} week {run.week} &middot; kickoff {run.first_kickoff}
        </h2>
        <span className="text-xs font-mono text-muted">
          {run.predicted_games} of {run.scheduled_games} games predicted
        </span>
      </div>
      <p className="mt-2 text-sm text-muted">{run.message}</p>
      <p className="mt-2 text-xs text-muted">
        Last checked {new Date(run.run_at).toLocaleString()}
      </p>
    </Card>
  );
}

function topDrivers(game: WeeklyGame) {
  return [...game.drivers]
    .sort((a, b) => Math.abs(b.contribution) - Math.abs(a.contribution))
    .slice(0, 2)
    .map(
      (d) =>
        `${featureLabel(d.feature)} → ${
          d.contribution >= 0 ? game.home_team : game.away_team
        }`,
    );
}

function ProbBar({ game }: { game: WeeklyGame }) {
  return (
    <div className="flex items-center gap-3 min-w-56">
      <span className="w-16 shrink-0 whitespace-nowrap text-right text-xs text-muted">
        {game.away_team} {pct(game.away_prob, 0)}
      </span>
      <div className="flex h-2 flex-1 overflow-hidden rounded-full bg-gray-200">
        <div
          className="bg-gray-400"
          style={{ width: `${game.away_prob * 100}%` }}
        />
        <div className="bg-foreground" style={{ width: `${game.home_prob * 100}%` }} />
      </div>
      <span className="w-16 shrink-0 whitespace-nowrap text-xs">
        {pct(game.home_prob, 0)} {game.home_team}
      </span>
    </div>
  );
}

export default async function PredictionsPage({
  searchParams,
}: {
  searchParams: Promise<{ [key: string]: string | string[] | undefined }>;
}) {
  const [weeks, status] = await Promise.all([
    getPredictionWeeks(),
    // The status banner is optional: never let it take the page down.
    getPredictionStatus().catch(() => null),
  ]);
  const pending =
    status && status.predicted_games < status.scheduled_games ? status : null;

  if (weeks.length === 0) {
    return (
      <div className="mx-auto max-w-6xl px-6 py-12">
        <PageHeader eyebrow="Win probabilities" title="Weekly Predictions" />
        {pending && <StatusBanner run={pending} />}
        <Card>
          <p className="text-sm text-muted">
            No predictions stored yet. Run{" "}
            <code className="font-mono">python src/predict_week.py</code> to
            generate a week.
          </p>
        </Card>
      </div>
    );
  }

  const params = await searchParams;
  const season = Number(params.season) || weeks[0].season;
  const week = Number(params.week) || weeks[0].week;
  const selected = weeks.find((w) => w.season === season && w.week === week);
  const current = selected ?? weeks[0];

  const data = await getWeeklyPredictions(current.season, current.week);
  const seasons = [...new Set(weeks.map((w) => w.season))];
  const played = data.games.filter((g) => g.correct !== null);
  const correct = played.filter((g) => g.correct).length;
  const avgConfidence =
    data.games.reduce((sum, g) => sum + g.confidence, 0) / data.games.length;

  return (
    <div className="mx-auto max-w-6xl px-6 py-12">
      <PageHeader
        eyebrow="Win probabilities"
        title="Weekly Predictions"
        description="Home-team win probabilities from the saved model, built only from games played before each kickoff. Each pick shows the two features that moved it most."
      />

      <div className="mb-8 space-y-3">
        {seasons.map((s) => (
          <div key={s} className="flex flex-wrap items-center gap-2">
            <span className="w-14 text-xs font-medium uppercase tracking-widest text-muted">
              {s}
            </span>
            {weeks
              .filter((w) => w.season === s)
              .sort((a, b) => a.week - b.week)
              .map((w) => {
                const active = w.season === data.season && w.week === data.week;
                return (
                  <Link
                    key={`${w.season}-${w.week}`}
                    href={`/predictions?season=${w.season}&week=${w.week}`}
                    className={`rounded-full border px-3 py-1 text-xs font-mono transition-colors ${
                      active
                        ? "border-foreground bg-foreground text-background"
                        : "border-border text-muted hover:border-foreground hover:text-foreground"
                    }`}
                  >
                    Wk {w.week}
                  </Link>
                );
              })}
          </div>
        ))}
      </div>

      {pending && <StatusBanner run={pending} />}

      {data.in_sample && (
        <Card className="mb-8">
          <p className="text-sm">
            <span className="font-medium">Historical replay.</span>{" "}
            <span className="text-muted">
              The {data.season} season was part of this model&apos;s training
              data, so these are in-sample and flatter its accuracy. For
              honest out-of-sample results see Model Performance and Prediction
              History.
            </span>
          </p>
        </Card>
      )}

      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4 mb-10">
        <StatTile
          label="Games"
          value={String(data.games.length)}
          sublabel={`${data.season} week ${data.week}`}
        />
        <StatTile
          label="Avg. confidence"
          value={pct(avgConfidence)}
          sublabel="of the predicted winner"
        />
        <StatTile
          label="Results"
          value={played.length ? `${correct}/${played.length}` : "—"}
          sublabel={played.length ? "picks correct (in-sample)" : "not played yet"}
        />
        <StatTile
          label="Model"
          value={data.model_version}
          sublabel={`generated ${new Date(data.generated_at).toLocaleDateString()}`}
        />
      </div>

      <DataTable
        rowKey={(g) => g.game_id}
        rows={data.games}
        columns={[
          {
            header: "Date",
            render: (g) => g.game_date,
          },
          {
            header: "Matchup",
            render: (g) => `${g.away_team} @ ${g.home_team}`,
          },
          { header: "Pick", render: (g) => g.predicted_winner },
          { header: "Win probability", render: (g) => <ProbBar game={g} /> },
          {
            header: "Key drivers",
            render: (g) => (
              <span className="text-xs text-muted">
                {topDrivers(g).join(" · ")}
              </span>
            ),
          },
          {
            header: "Result",
            align: "right",
            render: (g) =>
              g.correct === null
                ? "—"
                : `${g.away_score}–${g.home_score} ${g.correct ? "✓" : "✗"}`,
          },
        ]}
      />

      <p className="mt-6 text-xs text-muted">
        A game is only predicted once both teams have five prior games in the
        season, so the first predictable week of a season is usually week 6.
        Drivers are standardized feature values times the model&apos;s
        coefficients; the team named is the one the feature favors.
      </p>
    </div>
  );
}
