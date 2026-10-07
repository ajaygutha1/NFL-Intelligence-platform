const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export type BacktestMetric = {
  test_season: number;
  games: number;
  accuracy: number;
  baseline_accuracy: number;
  log_loss: number;
  brier: number;
  roc_auc: number;
};

export type BacktestPrediction = {
  game_id: string;
  test_season: number;
  week: number;
  game_date: string;
  home_team: string;
  away_team: string;
  home_score: number;
  away_score: number;
  home_prob: number;
  predicted_home_win: number;
  correct: number;
  confidence: number;
};

export type ModelInfo = {
  model_version: string;
  training_date: string;
  feature_cols: string[];
  training_seasons: number[];
};

export type ModelInsight = {
  feature: string;
  coefficient: number;
  permutation_importance: number;
  holdout_season: number;
};

export type WeekSummary = {
  season: number;
  week: number;
  games: number;
  generated_at: string;
};

export type FeatureDriver = {
  feature: string;
  contribution: number;
};

export type WeeklyGame = {
  game_id: string;
  game_date: string;
  home_team: string;
  away_team: string;
  home_prob: number;
  away_prob: number;
  predicted_winner: string;
  confidence: number;
  drivers: FeatureDriver[];
  home_score: number | null;
  away_score: number | null;
  correct: boolean | null;
};

export type WeeklyPredictions = {
  season: number;
  week: number;
  generated_at: string;
  model_version: string;
  in_sample: boolean;
  games: WeeklyGame[];
};

async function apiGet<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE_URL}${path}`, { cache: "no-store" });

  if (!res.ok) {
    throw new Error(`API request failed: ${path} (${res.status})`);
  }

  return res.json() as Promise<T>;
}

export function getBacktestMetrics() {
  return apiGet<BacktestMetric[]>("/api/backtest/metrics");
}

export function getBacktestPredictions(season?: number) {
  const query = season ? `?season=${season}` : "";
  return apiGet<BacktestPrediction[]>(`/api/backtest/predictions${query}`);
}

export function getModelInfo() {
  return apiGet<ModelInfo>("/api/model/info");
}

export function getModelInsights() {
  return apiGet<ModelInsight[]>("/api/model/insights");
}

export function getPredictionWeeks() {
  return apiGet<WeekSummary[]>("/api/predictions/weeks");
}

export function getWeeklyPredictions(season: number, week: number) {
  return apiGet<WeeklyPredictions>(`/api/predictions/week/${season}/${week}`);
}
