import { ImportanceChart } from "@/components/ImportanceChart";
import { Card } from "@/components/ui/Card";
import { DataTable } from "@/components/ui/DataTable";
import { PageHeader } from "@/components/ui/PageHeader";
import { getModelInsights } from "@/lib/api";
import { featureLabel } from "@/lib/features";

export const dynamic = "force-dynamic";

export default async function InsightsPage() {
  const insights = await getModelInsights();
  const holdout = insights[0]?.holdout_season;

  return (
    <div className="mx-auto max-w-6xl px-6 py-12">
      <PageHeader
        eyebrow="What drives the model"
        title="Model Insights"
        description="Two views of feature importance. Coefficients show how the model weighs each input; permutation importance shows how much accuracy actually depends on it."
      />

      <div className="grid gap-4 lg:grid-cols-2 mb-10">
        <Card>
          <h2 className="text-sm font-medium">Logistic regression coefficients</h2>
          <p className="mt-1 mb-4 text-xs text-muted">
            Change in home-win log-odds per one standard deviation of the
            home-minus-away difference. Solid bars push toward the home team,
            gray bars toward the away team. Defensive EPA is EPA allowed, so its
            weight is negative: the more a team allows, the worse its odds.
          </p>
          <ImportanceChart insights={insights} metric="coefficient" digits={3} />
        </Card>
        <Card>
          <h2 className="text-sm font-medium">Permutation importance</h2>
          <p className="mt-1 mb-4 text-xs text-muted">
            Increase in log loss when the feature is shuffled on the {holdout}{" "}
            holdout season (model trained on earlier seasons only). Higher means
            the model leans on it more; below zero means it adds nothing.
          </p>
          <ImportanceChart
            insights={insights}
            metric="permutation_importance"
            digits={4}
          />
        </Card>
      </div>

      <DataTable
        rowKey={(i) => i.feature}
        rows={insights}
        columns={[
          { header: "Feature", render: (i) => featureLabel(i.feature) },
          {
            header: "Coefficient",
            render: (i) => i.coefficient.toFixed(3),
            align: "right",
          },
          {
            header: "Permutation importance",
            render: (i) => i.permutation_importance.toFixed(4),
            align: "right",
          },
        ]}
      />

      <p className="mt-6 max-w-2xl text-xs text-muted">
        The two rankings differ because offensive EPA, passing EPA and success
        rate are highly correlated (r ≈ 0.75&ndash;0.93), so the coefficients
        split credit among them and shuffling any one is cushioned by the
        others. Defensive EPA is nearly independent of everything else, so
        shuffling it removes information nothing else supplies. Coefficients
        are fit on seasons before {holdout}; permutation scores are measured on{" "}
        {holdout}. Both are computed in the training script, never per request.
      </p>
    </div>
  );
}
