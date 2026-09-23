import { DataTable } from "@/components/ui/DataTable";
import { PageHeader } from "@/components/ui/PageHeader";
import { StatTile } from "@/components/ui/StatTile";
import { getWeeklyPredictions } from "@/lib/api";


export const dynamic = "force-dynamic";

const SEASON = 2025;
const WEEK = 12;


export default async function PredictionsPage() {
  const predictions = await getWeeklyPredictions(
    SEASON,
    WEEK,
  );

  const generatedAt =
    predictions.length > 0
      ? predictions[0].generated_at
      : null;

  return (
    <div className="mx-auto max-w-6xl px-6 py-12">
      <PageHeader
        eyebrow="Weekly model output"
        title="Weekly Predictions"
        description={`NFL win probabilities for ${SEASON} Week ${WEEK}, generated from the trained model and stored by the offline prediction pipeline.`}
      />

      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4 mb-10">
        <StatTile
          label="Season"
          value={String(SEASON)}
        />

        <StatTile
          label="Week"
          value={String(WEEK)}
        />

        <StatTile
          label="Games"
          value={String(predictions.length)}
        />

        <StatTile
          label="Generated"
          value={
            generatedAt
              ? new Date(
                  generatedAt,
                ).toLocaleDateString()
              : "—"
          }
          sublabel={
            generatedAt
              ? new Date(
                  generatedAt,
                ).toLocaleTimeString()
              : "Run predict_week.py"
          }
        />
      </div>

      {predictions.length > 0 ? (
        <DataTable
          rowKey={(row) => row.game_id}
          rows={predictions}
          columns={[
            {
              header: "Away",
              render: (row) => row.away_team,
            },
            {
              header: "Home",
              render: (row) => row.home_team,
            },
            {
              header: "Away win",
              render: (row) =>
                `${(row.away_prob * 100).toFixed(1)}%`,
              align: "right",
            },
            {
              header: "Home win",
              render: (row) =>
                `${(row.home_prob * 100).toFixed(1)}%`,
              align: "right",
            },
            {
              header: "Predicted winner",
              render: (row) =>
                row.predicted_winner,
            },
          ]}
        />
      ) : (
        <div className="rounded-xl border border-border p-6 text-sm text-muted">
          No predictions are stored for this week yet.
          Run the weekly prediction script first.
        </div>
      )}
    </div>
  );
}
