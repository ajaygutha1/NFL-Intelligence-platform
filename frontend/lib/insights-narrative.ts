import type { ModelInsight } from "@/lib/api";
import { featureLabel } from "@/lib/features";

export type Takeaway = { title: string; body: string };

// Importance below this (in log-loss units) is treated as "adds little": on one
// season of ~190 games, differences this small are within noise.
const WEAK_IMPORTANCE = 0.005;

const signed = (n: number) => `${n >= 0 ? "+" : "−"}${Math.abs(n).toFixed(2)}`;

/**
 * Plain-English takeaways computed from the model's actual numbers, so they stay
 * true when the model is retrained instead of going stale like hand-written text.
 */
export function buildTakeaways(insights: ModelInsight[]): Takeaway[] {
  if (insights.length === 0) return [];

  const holdout = insights[0].holdout_season;
  const byImportance = [...insights].sort(
    (a, b) => b.permutation_importance - a.permutation_importance,
  );
  const byWeight = [...insights].sort(
    (a, b) => Math.abs(b.coefficient) - Math.abs(a.coefficient),
  );

  const top = byImportance[0];
  const runnerUp = byImportance[1];
  const heaviest = byWeight[0];
  const weak = byImportance.filter(
    (i) => i.permutation_importance < WEAK_IMPORTANCE,
  );

  const takeaways: Takeaway[] = [];

  const ratio =
    runnerUp && runnerUp.permutation_importance > 0
      ? top.permutation_importance / runnerUp.permutation_importance
      : null;
  takeaways.push({
    title: `${featureLabel(top.feature)} is what the model depends on most`,
    body:
      `Shuffling ${featureLabel(top.feature)} across the ${holdout} games made the ` +
      `model's predictions worse by ${top.permutation_importance.toFixed(3)} log loss` +
      (ratio && runnerUp
        ? `, about ${ratio.toFixed(1)}× the next feature (${featureLabel(runnerUp.feature)}, ${runnerUp.permutation_importance.toFixed(3)}). `
        : ". ") +
      "The bigger the damage from scrambling a feature, the more the predictions rely on it.",
  });

  takeaways.push(
    heaviest.feature === top.feature
      ? {
          title: "The two charts agree on the leader",
          body: `${featureLabel(heaviest.feature)} has both the largest weight (${signed(heaviest.coefficient)}) and the largest importance, so the model both weighs it heavily and genuinely needs it.`,
        }
      : {
          title: "Biggest weight is not the same as most useful",
          body:
            `${featureLabel(heaviest.feature)} has the largest weight (${signed(heaviest.coefficient)}), ` +
            `yet ${featureLabel(top.feature)} matters more when scrambled. ` +
            "Several offensive features carry overlapping information, so the model splits credit among " +
            "them and no single one is irreplaceable. A feature with unique information " +
            "can have a smaller weight and still be the hardest to lose.",
        },
  );

  takeaways.push(
    weak.length > 0
      ? {
          title: `${weak.map((w) => featureLabel(w.feature)).join(", ")} add${weak.length === 1 ? "s" : ""} little`,
          body: `Scrambling ${weak.length === 1 ? "it" : "any of them"} changes accuracy by less than ${WEAK_IMPORTANCE.toFixed(3)}, which is within the noise of a single season. ${weak.some((w) => w.permutation_importance < 0) ? "A negative score means shuffling it made predictions slightly better, so the model gains nothing from it. " : ""}A feature can look sensible on its own and still add nothing once the others are in the model.`,
        }
      : {
          title: "Every feature contributes",
          body: `Scrambling any of the ${insights.length} features made predictions worse by more than ${WEAK_IMPORTANCE.toFixed(3)}, so none is dead weight.`,
        },
  );

  return takeaways;
}

export type GlossaryEntry = { term: string; definition: string };

export const GLOSSARY: GlossaryEntry[] = [
  {
    term: "EPA (expected points added)",
    definition:
      "Every play changes a team's chance of scoring. EPA is the change in expected points from before the play to after it. A 40-yard completion is strongly positive; a fumble returned for a touchdown is very negative.",
  },
  {
    term: "Home minus away",
    definition:
      "Each feature compares the two teams: the home team's recent number minus the away team's. Positive favors the team whose number is higher, except defensive EPA, where lower is better.",
  },
  {
    term: "Coefficient",
    definition:
      "How hard the model pushes on a feature. It is measured in log-odds (a scale where 0 means a coin flip), per one standard deviation of the difference. Positive pushes toward the home team, negative toward the away team. It is not a fixed percentage-point change, because the same push moves a 50% game more than a 90% game.",
  },
  {
    term: "Permutation importance",
    definition:
      "A usefulness test: randomly shuffle one feature so it carries no real information, then see how much worse the predictions get. Bigger damage means the model leaned on that feature more.",
  },
  {
    term: "Log loss",
    definition:
      "The score used for that damage. It punishes confident wrong predictions heavily, so lower is better. A rise of 0.07 is large for this model; a rise of 0.001 is nothing.",
  },
  {
    term: "Holdout season",
    definition:
      "Importance is measured on a season the model did not train on, so it reflects how the model behaves on games it has never seen.",
  },
];

export const CAVEATS: string[] = [
  "These describe what this model uses, not what causes wins. A feature can be useful for prediction without being the reason teams win.",
  "Importance is measured on one season (about 190 games). Small differences between features are noise; only the large gaps are reliable.",
  "The model sees six summaries of each team's last five games. It does not know about injuries, quarterbacks, weather, or betting lines.",
];
