from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import BacktestMetric, BacktestPrediction, Game
from app.schemas import BacktestMetricOut, BacktestPredictionOut

router = APIRouter(prefix="/api/backtest", tags=["backtest"])


@router.get("/metrics", response_model=list[BacktestMetricOut])
def list_backtest_metrics(db: Session = Depends(get_db)):
    return (
        db.query(BacktestMetric)
        .order_by(BacktestMetric.test_season)
        .all()
    )


@router.get("/predictions", response_model=list[BacktestPredictionOut])
def list_backtest_predictions(
    season: int | None = Query(default=None),
    db: Session = Depends(get_db),
):
    query = (
        db.query(BacktestPrediction, Game)
        .join(Game, BacktestPrediction.game_id == Game.game_id)
    )

    if season is not None:
        query = query.filter(BacktestPrediction.test_season == season)

    rows = query.order_by(
        BacktestPrediction.test_season, Game.week
    ).all()

    return [
        BacktestPredictionOut(
            game_id=prediction.game_id,
            test_season=prediction.test_season,
            home_team=game.home_team,
            away_team=game.away_team,
            home_prob=prediction.home_prob,
            predicted_home_win=prediction.predicted_home_win,
            correct=prediction.correct,
            confidence=prediction.confidence,
        )
        for prediction, game in rows
    ]
