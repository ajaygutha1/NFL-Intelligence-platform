"""Populates the SQLite DB from the ML pipeline's CSV/joblib outputs.

Re-run this any time `notebooks/03_backtest.py` regenerates the CSVs or the
model bundle. Safe to run repeatedly: it wipes and re-creates every table
each time (weekly_predictions included, since it's owned by the weekly
prediction pipeline, not this script, once that pipeline exists).
"""

import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config import (  # noqa: E402
    BACKTEST_METRICS_CSV,
    BACKTEST_PREDICTIONS_CSV,
    MODEL_DATA_CSV,
)
from app.database import Base, SessionLocal, engine  # noqa: E402
from app.ml import get_model_info  # noqa: E402
from app.models import (  # noqa: E402
    BacktestMetric,
    BacktestPrediction,
    Game,
    ModelVersion,
    WeeklyPrediction,
)


def seed():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()

    try:
        model_data = pd.read_csv(MODEL_DATA_CSV)

        games = [
            Game(
                game_id=row["game_id"],
                season=int(row["season"]),
                week=int(row["week"]),
                game_date=row["game_date"],
                home_team=row["home_team"],
                away_team=row["away_team"],
                diff_off_epa=row["diff_off_epa"],
                diff_def_epa=row["diff_def_epa"],
                diff_pass_epa=row["diff_pass_epa"],
                diff_rush_epa=row["diff_rush_epa"],
                diff_success_rate=row["diff_success_rate"],
                diff_rest_days=row["diff_rest_days"],
                home_score=int(row["home_score"]),
                away_score=int(row["away_score"]),
                home_win=int(row["home_win"]),
            )
            for _, row in model_data.iterrows()
        ]
        db.bulk_save_objects(games)
        print(f"Seeded {len(games)} games")

        backtest_predictions = pd.read_csv(BACKTEST_PREDICTIONS_CSV)

        predictions = [
            BacktestPrediction(
                game_id=row["game_id"],
                test_season=int(row["season"]),
                home_prob=row["home_prob"],
                predicted_home_win=int(row["predicted_home_win"]),
                correct=int(row["correct"]),
                confidence=row["confidence"],
            )
            for _, row in backtest_predictions.iterrows()
        ]
        db.bulk_save_objects(predictions)
        print(f"Seeded {len(predictions)} backtest predictions")

        backtest_metrics = pd.read_csv(BACKTEST_METRICS_CSV)

        metrics = [
            BacktestMetric(
                test_season=int(row["test_season"]),
                games=int(row["games"]),
                accuracy=row["accuracy"],
                baseline_accuracy=row["baseline_accuracy"],
                log_loss=row["log_loss"],
                brier=row["brier"],
                roc_auc=row["roc_auc"],
            )
            for _, row in backtest_metrics.iterrows()
        ]
        db.bulk_save_objects(metrics)
        print(f"Seeded {len(metrics)} backtest metric rows")

        info = get_model_info()
        db.add(
            ModelVersion(
                model_version=info["model_version"],
                training_date=info["training_date"],
                feature_cols=json.dumps(info["feature_cols"]),
                training_seasons=json.dumps(info["training_seasons"]),
            )
        )
        print(f"Seeded model version {info['model_version']}")

        db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    seed()
