from sqlalchemy import Column, Float, ForeignKey, Integer, String

from app.database import Base


class Game(Base):
    __tablename__ = "games"

    game_id = Column(String, primary_key=True)
    season = Column(Integer, nullable=False)
    week = Column(Integer, nullable=False)
    game_date = Column(String, nullable=False)
    home_team = Column(String, nullable=False)
    away_team = Column(String, nullable=False)

    diff_off_epa = Column(Float)
    diff_def_epa = Column(Float)
    diff_pass_epa = Column(Float)
    diff_rush_epa = Column(Float)
    diff_success_rate = Column(Float)
    diff_rest_days = Column(Float)

    home_score = Column(Integer)
    away_score = Column(Integer)
    home_win = Column(Integer)


class BacktestPrediction(Base):
    __tablename__ = "backtest_predictions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    game_id = Column(String, ForeignKey("games.game_id"), nullable=False)
    test_season = Column(Integer, nullable=False)

    home_prob = Column(Float, nullable=False)
    predicted_home_win = Column(Integer, nullable=False)
    correct = Column(Integer, nullable=False)
    confidence = Column(Float, nullable=False)


class BacktestMetric(Base):
    __tablename__ = "backtest_metrics"

    test_season = Column(Integer, primary_key=True)
    games = Column(Integer, nullable=False)
    accuracy = Column(Float, nullable=False)
    baseline_accuracy = Column(Float, nullable=False)
    log_loss = Column(Float, nullable=False)
    brier = Column(Float, nullable=False)
    roc_auc = Column(Float, nullable=False)


class ModelVersion(Base):
    __tablename__ = "model_versions"

    model_version = Column(String, primary_key=True)
    training_date = Column(String, nullable=False)
    feature_cols = Column(String, nullable=False)  # JSON-encoded list
    training_seasons = Column(String, nullable=False)  # JSON-encoded list


class WeeklyPrediction(Base):
    """Populated by Ajay's Weekly Predictions task, not the seed script."""

    __tablename__ = "weekly_predictions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    season = Column(Integer, nullable=False)
    week = Column(Integer, nullable=False)
    generated_at = Column(String, nullable=False)
    game_id = Column(String, nullable=False)
    home_team = Column(String, nullable=False)
    away_team = Column(String, nullable=False)
    home_prob = Column(Float, nullable=False)
    away_prob = Column(Float, nullable=False)
    predicted_winner = Column(String, nullable=False)
