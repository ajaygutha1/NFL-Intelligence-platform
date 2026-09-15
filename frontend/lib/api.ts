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
  home_team: string;
  away_team: string;
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
