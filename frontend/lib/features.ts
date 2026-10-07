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
