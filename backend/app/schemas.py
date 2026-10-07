from pydantic import BaseModel, ConfigDict


class BacktestMetricOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    test_season: int
    games: int
    accuracy: float
    baseline_accuracy: float
    log_loss: float
    brier: float
    roc_auc: float


class BacktestPredictionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    game_id: str
    test_season: int
    week: int
    game_date: str
    home_team: str
    away_team: str
    home_score: int
    away_score: int
    home_prob: float
    predicted_home_win: int
    correct: int
    confidence: float


class ModelInfoOut(BaseModel):
    model_version: str
    training_date: str
    feature_cols: list[str]
    training_seasons: list[int]


class ModelInsightOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    feature: str
    coefficient: float
    permutation_importance: float
    holdout_season: int


class WeekSummaryOut(BaseModel):
    season: int
    week: int
    games: int
    generated_at: str


class FeatureDriverOut(BaseModel):
    feature: str
    contribution: float


class WeeklyGameOut(BaseModel):
    game_id: str
    game_date: str
    home_team: str
    away_team: str
    home_prob: float
    away_prob: float
    predicted_winner: str
    confidence: float
    drivers: list[FeatureDriverOut]
    home_score: int | None = None
    away_score: int | None = None
    correct: bool | None = None


class WeeklyPredictionsOut(BaseModel):
    season: int
    week: int
    generated_at: str
    model_version: str
    # True when the season was part of the model's training data, i.e. a
    # replay of a past week rather than a genuine out-of-sample forecast.
    in_sample: bool
    games: list[WeeklyGameOut]
