// Plain-English names for the model's six home-minus-away difference features.
export const FEATURE_LABELS: Record<string, string> = {
  diff_off_epa: "Offensive EPA",
  diff_def_epa: "Defensive EPA",
  diff_pass_epa: "Passing EPA",
  diff_rush_epa: "Rushing EPA",
  diff_success_rate: "Success rate",
  diff_rest_days: "Rest days",
};

export function featureLabel(feature: string) {
  return FEATURE_LABELS[feature] ?? feature;
}

export function pct(value: number, digits = 1) {
  return `${(value * 100).toFixed(digits)}%`;
}

// What each feature measures, in plain English. All are home minus away, each
// team's last five games before kickoff (never including the game itself).
export const FEATURE_DESCRIPTIONS: Record<string, string> = {
  diff_off_epa:
    "How many expected points per play each offense has been adding lately.",
  diff_def_epa:
    "How many expected points per play each defense has been giving up lately. Lower is better.",
  diff_pass_epa: "Expected points added per passing play, recently.",
  diff_rush_epa: "Expected points added per rushing play, recently.",
  diff_success_rate:
    "The share of plays that kept the offense on schedule (gaining enough yardage for the down).",
  diff_rest_days: "Days since each team's previous game.",
};

export function featureDescription(feature: string) {
  return FEATURE_DESCRIPTIONS[feature] ?? "";
}
