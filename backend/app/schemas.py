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
    home_team: str
    away_team: str
    home_prob: float
    predicted_home_win: int
    correct: int
    confidence: float


class ModelInfoOut(BaseModel):
    model_version: str
    training_date: str
    feature_cols: list[str]
    training_seasons: list[int]
