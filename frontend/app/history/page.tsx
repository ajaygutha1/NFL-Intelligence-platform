import { HistoryExplorer } from "@/components/HistoryExplorer";
import { PageHeader } from "@/components/ui/PageHeader";
import { getBacktestPredictions } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function HistoryPage() {
  const predictions = await getBacktestPredictions();

  return (
    <div className="mx-auto max-w-6xl px-6 py-12">
      <PageHeader
        eyebrow="Walk-forward backtest"
        title="Prediction History"
        description="Every backtested game, predicted using only seasons before it. Filter by season or result, and sort by confidence to see where the model was most sure — and most wrong."
      />
      <HistoryExplorer predictions={predictions} />
    </div>
  );
}
